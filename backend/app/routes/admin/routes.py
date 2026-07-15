from flask import (
    render_template, redirect, url_for, flash, request, session, abort, Response,
    current_app,
)
from flask_login import login_user, login_required, logout_user, current_user
from datetime import datetime
import csv
import io
import random
import secrets

from app.extensions import db, limiter, login_manager
from app.models.user import User, TwoFactorCode
from app.models.audit import ActivityLog
from app.forms.admin import (
    AdminUserCreateForm,
    AdminUserUpdateForm,
    DeleteUserForm,
)
from app.services.mail_service import send_2fa_email
from app.utils.logging_helper import log_activity

from . import admin_bp

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def require_superuser():
    if current_user.is_superuser:
        return
    log_activity(
        action='UNAUTHORIZED_ACCESS',
        details='Intento de acceso a gestión de administradores sin privilegios.',
        user=current_user,
    )
    abort(403)


def active_superuser_count():
    return User.query.filter_by(is_superuser=True, is_active=True).count()


@admin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('admin.dashboard'))
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        session['captcha_result'] = num1 + num2
        captcha_question = f"¿Cuánto es {num1} + {num2}?"
        return render_template('admin/login.html', captcha_question=captcha_question)

    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    captcha_answer = request.form.get('captcha', '')

    stored_captcha = session.get('captcha_result')
    if not stored_captcha or str(captcha_answer) != str(stored_captcha):
        session.pop('captcha_result', None)
        flash('Captcha incorrecto. Intenta de nuevo.', 'error')
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        session['captcha_result'] = num1 + num2
        captcha_question = f"¿Cuánto es {num1} + {num2}?"
        return render_template('admin/login.html', captcha_question=captcha_question)

    session.pop('captcha_result', None)

    user = User.query.filter_by(email=email).first()
    if user and user.is_active and user.check_password(password):
        # Invalidate previous unused 2FA codes
        TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None).update({'consumed_at': datetime.utcnow()})

        code = ''.join([secrets.choice('0123456789') for _ in range(6)])
        tf_code = TwoFactorCode(user_id=user.id, code=code)
        db.session.add(tf_code)
        db.session.commit()

        # Only log code to stdout if explicitly enabled
        if current_app.config.get('ENABLE_2FA_CODE_LOGGING', False):
            current_app.logger.info(f"[DEV] 2FA code for {user.email}: {code}")

        send_2fa_email(user.email, code)
        session['2fa_user_id'] = user.id
        flash('Código de verificación enviado a tu correo.', 'info')
        return redirect(url_for('admin.verify_2fa'))

    flash('Email o contraseña inválidos.', 'error')
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    session['captcha_result'] = num1 + num2
    captcha_question = f"¿Cuánto es {num1} + {num2}?"
    return render_template('admin/login.html', captcha_question=captcha_question)


@admin_bp.route('/2fa', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def verify_2fa():
    user_id = session.get('2fa_user_id')
    if not user_id:
        return redirect(url_for('admin.login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('2fa_user_id', None)
        return redirect(url_for('admin.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        tf_code = TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None) \
            .order_by(TwoFactorCode.created_at.desc()).first()

        if tf_code:
            # Increment attempts
            tf_code.attempts += 1
            db.session.flush()

            max_attempts = current_app.config.get('MAX_2FA_ATTEMPTS', 5)
            if tf_code.attempts > max_attempts:
                tf_code.consumed_at = datetime.utcnow()
                db.session.commit()
                flash('Demasiados intentos. Solicita un nuevo código.', 'error')
                return redirect(url_for('admin.login'))

            if tf_code.verify_code(code):
                tf_code.consumed_at = datetime.utcnow()
                user.last_login_at = datetime.utcnow()
                db.session.commit()
                # Regenerate session to prevent fixation
                session.clear()
                login_user(user)
                session['2fa_completed'] = True
                log_activity(
                    action='LOGIN',
                    details='Inicio de sesión exitoso con 2FA',
                    user=user
                )
                flash('Sesión iniciada correctamente.', 'success')
                return redirect(url_for('admin.dashboard'))

        flash('Código inválido o expirado.', 'error')

    return render_template('admin/verify_2fa.html')


@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    from flask_wtf import validate_csrf
    log_activity(
        action='LOGOUT',
        details='Cierre de sesión manual',
        user=current_user
    )
    logout_user()
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    from app.models.article import Article
    from app.models.media_asset import MediaAsset

    total_articles = Article.query.filter(Article.deleted_at.is_(None)).count()
    published = Article.query.filter_by(status="published", deleted_at=None).count()
    drafts = Article.query.filter_by(status="draft", deleted_at=None).count()
    review = Article.query.filter_by(status="review", deleted_at=None).count()
    archived = Article.query.filter_by(status="archived", deleted_at=None).count()

    total_media = MediaAsset.query.filter(MediaAsset.deleted_at.is_(None)).count()
    total_media_bytes = db.session.query(db.func.coalesce(db.func.sum(MediaAsset.size_bytes), 0)) \
        .filter(MediaAsset.deleted_at.is_(None)).scalar() or 0

    recent_articles = Article.query.filter(Article.deleted_at.is_(None)) \
        .order_by(Article.updated_at.desc()).limit(5).all()

    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()

    stats = {
        'total_articles': total_articles,
        'published': published,
        'drafts': drafts,
        'review': review,
        'archived': archived,
        'total_media': total_media,
        'total_media_bytes': total_media_bytes,
    }

    return render_template('admin/dashboard.html', stats=stats,
                           recent_articles=recent_articles, recent_logs=recent_logs)


# Article management routes
@admin_bp.route('/articles')
@login_required
def article_list():
    from app.models.article import Article
    from app.models.category import Category

    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    cat_filter = request.args.get('category', '').strip()

    query = Article.query.filter(Article.deleted_at.is_(None))
    if q:
        query = query.filter(Article.title.ilike(f"%{q}%"))
    if status_filter:
        query = query.filter(Article.status == status_filter)
    if cat_filter:
        query = query.filter(Article.category_id == int(cat_filter))

    pagination = query.order_by(Article.updated_at.desc()).paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.order_by(Category.name).all()

    return render_template('admin/article_list.html', pagination=pagination, categories=categories,
                           q=q, status_filter=status_filter, cat_filter=cat_filter)


@admin_bp.route('/articles/new')
@login_required
def article_create():
    return render_template('admin/article_editor.html', article=None)


@admin_bp.route('/articles/<int:article_id>/edit')
@login_required
def article_edit(article_id):
    from app.models.article import Article
    article = Article.query.get_or_404(article_id)
    return render_template('admin/article_editor.html', article=article)


@admin_bp.route('/articles/<int:article_id>/revisions')
@login_required
def article_revisions(article_id):
    from app.models.article import Article
    article = Article.query.get_or_404(article_id)
    return render_template('admin/article_revisions.html', article=article)


@admin_bp.route('/media')
@login_required
def media_library():
    return render_template('admin/media_library.html')


# Existing routes below
@admin_bp.route('/logs')
@login_required
def view_logs():
    if not current_user.is_superuser:
        log_activity(
            action='UNAUTHORIZED_ACCESS',
            details='Intento de acceso a logs sin privilegios de super admin.',
            user=current_user,
        )
        abort(403)

    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('username', '').strip()
    date_filter = request.args.get('date', '').strip()

    query = ActivityLog.query
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)
    if user_filter:
        query = query.filter(ActivityLog.username == user_filter)
    if date_filter:
        query = query.filter(db.func.date(ActivityLog.created_at) == date_filter)

    pagination = query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False,
    )
    actions = sorted({action[0] for action in db.session.query(ActivityLog.action).distinct()})
    users = sorted({username[0] for username in db.session.query(ActivityLog.username).distinct() if username[0]})

    return render_template(
        'admin/audit_logs.html', logs=pagination, actions=actions, users=users,
        current_action=action_filter, current_username=user_filter, current_date=date_filter,
    )


@admin_bp.route('/logs/export')
@login_required
def export_logs():
    if not current_user.is_superuser:
        abort(403)

    query = ActivityLog.query
    action_filter = request.args.get('action', '').strip()
    user_filter = request.args.get('username', '').strip()
    date_filter = request.args.get('date', '').strip()
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter)
    if user_filter:
        query = query.filter(ActivityLog.username == user_filter)
    if date_filter:
        query = query.filter(db.func.date(ActivityLog.created_at) == date_filter)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Fecha', 'Usuario', 'Acción', 'Detalles', 'IP', 'User Agent'])
    for log in query.order_by(ActivityLog.created_at.desc()).all():
        writer.writerow([
            log.id, log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else '',
            log.username or (log.user.email if log.user else 'Sistema'),
            log.action, log.details or '', log.ip_address or '', log.user_agent or '',
        ])

    filename = f"auditoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})


@admin_bp.route('/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    require_superuser()

    create_form = AdminUserCreateForm(prefix='create')
    delete_form = DeleteUserForm(prefix='delete')

    if create_form.validate_on_submit():
        username = create_form.username.data.strip()
        email = create_form.email.data.strip().lower()

        existing_email = User.query.filter(db.func.lower(User.email) == email).first()
        existing_username = User.query.filter(db.func.lower(User.username) == username.lower()).first()

        if existing_email:
            flash('Ya existe un usuario con ese correo.', 'error')
        elif existing_username:
            flash('Ya existe un usuario con ese nombre.', 'error')
        else:
            user = User(username=username, email=email, is_active=True,
                        is_superuser=create_form.is_superuser.data)
            user.set_password(create_form.password.data)
            db.session.add(user)
            db.session.commit()
            role_label = 'Super Admin' if user.is_superuser else 'Administrador'
            log_activity(action='CREATE_ADMIN_USER',
                         details=f'{role_label} creado: {user.username} ({user.email})',
                         user=current_user)
            flash(f'{role_label} creado correctamente.', 'success')
            return redirect(url_for('admin.manage_users'))

    users = User.query.order_by(User.is_active.desc(), User.is_superuser.desc(), User.created_at.desc()).all()
    return render_template('admin/users.html', create_form=create_form, delete_form=delete_form, users=users)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    require_superuser()

    user = User.query.get_or_404(id)
    form = AdminUserUpdateForm(prefix='edit', obj=user)
    delete_form = DeleteUserForm(prefix='delete')

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        existing_email = User.query.filter(db.func.lower(User.email) == email, User.id != user.id).first()
        existing_username = User.query.filter(db.func.lower(User.username) == username.lower(), User.id != user.id).first()

        if existing_email:
            flash('Ya existe un usuario con ese correo.', 'error')
        elif existing_username:
            flash('Ya existe un usuario con ese nombre.', 'error')
        elif user.id == current_user.id and not form.is_active.data:
            flash('No puedes desactivar tu propio usuario mientras tienes la sesión activa.', 'error')
        elif user.is_superuser and not form.is_active.data and active_superuser_count() <= 1:
            flash('No puedes desactivar al último super admin activo.', 'error')
        else:
            user.username = username
            user.email = email
            user.is_active = form.is_active.data
            if form.password.data:
                user.set_password(form.password.data)
            db.session.commit()
            log_activity(action='UPDATE_ADMIN_USER',
                         details=f'Usuario de panel actualizado: {user.username} ({user.email})',
                         user=current_user)
            flash('Usuario actualizado correctamente.', 'success')
            return redirect(url_for('admin.manage_users'))

    return render_template('admin/user_edit.html', delete_form=delete_form, form=form, managed_user=user)


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    require_superuser()

    form = DeleteUserForm(prefix='delete')
    if not form.validate_on_submit():
        abort(400)

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario activo.', 'error')
        return redirect(url_for('admin.manage_users'))

    if user.is_superuser and active_superuser_count() <= 1:
        flash('No puedes eliminar al último super admin activo.', 'error')
        return redirect(url_for('admin.manage_users'))

    if bool(user.activity_logs):
        user.is_active = False
        db.session.commit()
        log_activity(action='DEACTIVATE_ADMIN_USER',
                     details=f'Usuario desactivado: {user.username} ({user.email})',
                     user=current_user)
        flash('El usuario fue desactivado para conservar la auditoría.', 'info')
    else:
        username = user.username
        email = user.email
        db.session.delete(user)
        db.session.commit()
        log_activity(action='DELETE_ADMIN_USER',
                     details=f'Usuario eliminado: {username} ({email})',
                     user=current_user)
        flash('Usuario eliminado correctamente.', 'success')

    return redirect(url_for('admin.manage_users'))