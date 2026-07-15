from flask import Blueprint, jsonify, request, session, abort, current_app
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.services.article_service import ArticleService, slugify
from app.services.article_query_service import ArticleQueryService
from app.services.publication_service import PublicationService
from app.services.revision_service import RevisionService
from app.services.media_service import MediaService
from app.services.taxonomy_service import CategoryService, TagService
from app.schemas.wiki_schemas import ArticleAdminSchema, CategorySchema, TagSchema, MediaAssetSchema, ArticleRevisionSchema
from app.utils.logging_helper import log_activity

admin_api_bp = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


def _error_response(code: str, message: str, status: int, details=None):
    from flask import g
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "requestId": getattr(g, "request_id", None),
        }
    }), status


def require_2fa_complete():
    if not current_user.is_authenticated:
        abort(401)
    if not session.get("2fa_completed"):
        abort(403)


def require_superuser():
    if not current_user.is_authenticated or not current_user.is_superuser:
        log_activity(action="UNAUTHORIZED_ACCESS", details="Intento de acceso admin API sin privilegios", user=current_user if current_user.is_authenticated else None)
        abort(403)


@admin_api_bp.before_request
def check_admin_auth():
    if request.method == "OPTIONS":
        return
    if not current_user.is_authenticated:
        return _error_response("UNAUTHORIZED", "No autorizado.", 401)


@admin_api_bp.route("/articles", methods=["GET"])
@login_required
def admin_list_articles():
    q = request.args.get("q", "").strip() or None
    status_filter = request.args.get("status") or None
    category = request.args.get("category") or None
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("perPage", 20, type=int), 1), 100)

    pagination = ArticleQueryService.list_admin(q=q, status=status_filter, category=category, page=page, per_page=per_page)
    schema = ArticleAdminSchema(many=True)

    return jsonify({
        "items": schema.dump(pagination.items),
        "pagination": {
            "page": pagination.page,
            "perPage": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "hasNext": pagination.has_next,
            "hasPrevious": pagination.has_prev,
        }
    })


@admin_api_bp.route("/articles", methods=["POST"])
@login_required
def admin_create_article():
    data = request.get_json()
    if not data:
        return _error_response("VALIDATION_ERROR", "Datos no válidos.", 400)
    if not data.get("title"):
        return _error_response("VALIDATION_ERROR", "El título es obligatorio.", 400, {"title": ["Campo obligatorio."]})

    try:
        article = ArticleService.create_article(data, current_user)
        schema = ArticleAdminSchema()
        return jsonify(schema.dump(article)), 201
    except Exception as e:
        db.session.rollback()
        return _error_response("INTERNAL_ERROR", str(e), 500)


@admin_api_bp.route("/articles/<int:article_id>", methods=["GET"])
@login_required
def admin_get_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)
    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>", methods=["PATCH"])
@login_required
def admin_update_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    data = request.get_json()
    if not data:
        return _error_response("VALIDATION_ERROR", "Datos no válidos.", 400)

    try:
        article = ArticleService.update_article(article, data, current_user)
        schema = ArticleAdminSchema()
        return jsonify(schema.dump(article))
    except ValueError as e:
        db.session.rollback()
        if "CONFLICT" in str(e):
            return _error_response("VERSION_CONFLICT", str(e), 409)
        return _error_response("VALIDATION_ERROR", str(e), 400)
    except Exception as e:
        db.session.rollback()
        return _error_response("INTERNAL_ERROR", str(e), 500)


@admin_api_bp.route("/articles/<int:article_id>", methods=["DELETE"])
@login_required
def admin_delete_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    force = request.args.get("force", "").lower() in ("true", "1")
    if force:
        if not current_user.is_superuser:
            return _error_response("FORBIDDEN", "Solo superusuarios pueden borrar físicamente.", 403)
        ArticleService.hard_delete(article, current_user)
        return "", 204

    ArticleService.soft_delete(article, current_user)
    return "", 204


@admin_api_bp.route("/articles/<int:article_id>/publish", methods=["POST"])
@login_required
def admin_publish_article(article_id):
    if not current_user.is_superuser:
        return _error_response("FORBIDDEN", "Solo superusuarios pueden publicar.", 403)

    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    is_valid, errors = PublicationService.publish(article, current_user)
    if not is_valid:
        return _error_response("VALIDATION_ERROR", "No se puede publicar.", 400, errors)

    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>/unpublish", methods=["POST"])
@login_required
def admin_unpublish_article(article_id):
    if not current_user.is_superuser:
        return _error_response("FORBIDDEN", "Solo superusuarios pueden retirar publicaciones.", 403)

    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    PublicationService.unpublish(article, current_user)
    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>/archive", methods=["POST"])
@login_required
def admin_archive_article(article_id):
    if not current_user.is_superuser:
        return _error_response("FORBIDDEN", "Solo superusuarios pueden archivar.", 403)

    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    ArticleService.archive(article, current_user)
    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>/restore", methods=["POST"])
@login_required
def admin_restore_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    ArticleService.restore(article, current_user)
    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>/duplicate", methods=["POST"])
@login_required
def admin_duplicate_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    new_article = ArticleService.duplicate(article, current_user)
    schema = ArticleAdminSchema()
    return jsonify(schema.dump(new_article)), 201


@admin_api_bp.route("/articles/<int:article_id>/revisions", methods=["GET"])
@login_required
def admin_list_revisions(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    revisions = RevisionService.list_revisions(article_id)
    schema = ArticleRevisionSchema(many=True)
    return jsonify(schema.dump(revisions))


@admin_api_bp.route("/articles/<int:article_id>/revisions/<int:revision_id>/restore", methods=["POST"])
@login_required
def admin_restore_revision(article_id, revision_id):
    if not current_user.is_superuser:
        return _error_response("FORBIDDEN", "Solo superusuarios pueden restaurar revisiones.", 403)

    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    result = RevisionService.restore_revision(article, revision_id, current_user)
    if not result:
        return _error_response("REVISION_NOT_FOUND", "Revisión no encontrada.", 404)

    schema = ArticleAdminSchema()
    return jsonify(schema.dump(article))


@admin_api_bp.route("/articles/<int:article_id>/autosave", methods=["POST"])
@login_required
def admin_autosave_article(article_id):
    article = ArticleQueryService.get_by_id(article_id)
    if not article:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    data = request.get_json()
    if not data:
        return _error_response("VALIDATION_ERROR", "Datos no válidos.", 400)

    try:
        article = ArticleService.autosave(article, data, current_user)
        schema = ArticleAdminSchema()
        return jsonify({"version": article.version, "updatedAt": article.updated_at.isoformat() if article.updated_at else None})
    except Exception as e:
        db.session.rollback()
        return _error_response("INTERNAL_ERROR", str(e), 500)


@admin_api_bp.route("/categories", methods=["GET", "POST"])
@login_required
def admin_categories():
    if request.method == "GET":
        cats = CategoryService.list_all()
        schema = CategorySchema(many=True)
        return jsonify(schema.dump(cats))
    else:
        data = request.get_json()
        if not data or not data.get("name"):
            return _error_response("VALIDATION_ERROR", "El nombre es obligatorio.", 400, {"name": ["Campo obligatorio."]})
        cat = CategoryService.create(
            name=data["name"],
            description=data.get("description"),
            sort_order=data.get("sortOrder", 0),
            is_active=data.get("isActive", True),
            user=current_user,
        )
        schema = CategorySchema()
        return jsonify(schema.dump(cat)), 201


@admin_api_bp.route("/categories/<int:cat_id>", methods=["PATCH", "DELETE"])
@login_required
def admin_category_detail(cat_id):
    cat = CategoryService.get(cat_id)
    if not cat:
        return _error_response("CATEGORY_NOT_FOUND", "Categoría no encontrada.", 404)

    if request.method == "PATCH":
        data = request.get_json()
        cat = CategoryService.update(cat, data, current_user)
        schema = CategorySchema()
        return jsonify(schema.dump(cat))
    else:
        if not current_user.is_superuser:
            return _error_response("FORBIDDEN", "Solo superusuarios pueden eliminar categorías.", 403)
        try:
            CategoryService.delete(cat, current_user)
            return "", 204
        except ValueError as e:
            return _error_response("CATEGORY_IN_USE", str(e), 409)


@admin_api_bp.route("/tags", methods=["GET", "POST"])
@login_required
def admin_tags():
    if request.method == "GET":
        tags = TagService.list_all()
        schema = TagSchema(many=True)
        return jsonify(schema.dump(tags))
    else:
        data = request.get_json()
        if not data or not data.get("name"):
            return _error_response("VALIDATION_ERROR", "El nombre es obligatorio.", 400, {"name": ["Campo obligatorio."]})
        tag = TagService.create(data["name"], current_user)
        schema = TagSchema()
        return jsonify(schema.dump(tag)), 201


@admin_api_bp.route("/tags/<int:tag_id>", methods=["DELETE"])
@login_required
def admin_tag_detail(tag_id):
    if not current_user.is_superuser:
        return _error_response("FORBIDDEN", "Solo superusuarios pueden eliminar etiquetas.", 403)
    from app.models.tag import Tag
    tag = Tag.query.get_or_404(tag_id)
    TagService.delete(tag, current_user)
    return "", 204


@admin_api_bp.route("/media", methods=["GET", "POST"])
@login_required
def admin_media():
    if request.method == "GET":
        q = request.args.get("q", "").strip() or None
        page = request.args.get("page", 1, type=int)
        per_page = min(max(request.args.get("perPage", 24, type=int), 1), 100)
        pagination = MediaService.list_media(q=q, page=page, per_page=per_page)
        schema = MediaAssetSchema(many=True)
        return jsonify({
            "items": schema.dump(pagination.items),
            "pagination": {
                "page": pagination.page,
                "perPage": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            }
        })
    else:
        if "file" not in request.files:
            return _error_response("VALIDATION_ERROR", "No se envió ningún archivo.", 400)

        file = request.files["file"]
        if not file.filename:
            return _error_response("VALIDATION_ERROR", "No se envió ningún archivo.", 400)

        try:
            asset = MediaService.upload(
                file,
                current_user,
                alt_text=request.form.get("altText"),
                caption=request.form.get("caption"),
                credit=request.form.get("credit"),
                license=request.form.get("license"),
                source_url=request.form.get("sourceUrl"),
            )
            schema = MediaAssetSchema()
            return jsonify(schema.dump(asset)), 201
        except ValueError as e:
            return _error_response("VALIDATION_ERROR", str(e), 400)
        except Exception as e:
            db.session.rollback()
            return _error_response("INTERNAL_ERROR", str(e), 500)


@admin_api_bp.route("/media/<uuid>", methods=["GET", "PATCH", "DELETE"])
@login_required
def admin_media_detail(uuid):
    asset = MediaService.get_by_uuid(uuid)
    if not asset:
        return _error_response("MEDIA_NOT_FOUND", "Imagen no encontrada.", 404)

    if request.method == "GET":
        schema = MediaAssetSchema()
        return jsonify(schema.dump(asset))
    elif request.method == "PATCH":
        data = request.get_json()
        asset = MediaService.update_metadata(asset, data, current_user)
        schema = MediaAssetSchema()
        return jsonify(schema.dump(asset))
    else:
        force = request.args.get("force", "").lower() in ("true", "1")
        if force and not current_user.is_superuser:
            return _error_response("FORBIDDEN", "Solo superusuarios pueden forzar eliminación.", 403)
        try:
            MediaService.soft_delete(asset, current_user)
            return "", 204
        except ValueError as e:
            return _error_response("MEDIA_IN_USE", str(e), 409)


@admin_api_bp.route("/media/<uuid>/usage", methods=["GET"])
@login_required
def admin_media_usage(uuid):
    usage = MediaService.check_usage(uuid)
    return jsonify({"usage": usage})