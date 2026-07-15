import logging
import uuid
import os
from flask import Flask, g, request, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import config
from .extensions import db, migrate, login_manager, csrf, mail, limiter, talisman, ma
from .services.minio_service import minio_service
from .error_handlers import register_error_handlers
from .commands import create_admin, rotate_secret, init_bucket, import_wiki_data
from .redis_utils import init_redis
from .health import health_bp
from .metrics import init_metrics
import logging.config


def _init_limiter_safe(app):
    """Inicializa Flask-Limiter con fallback automático a memory://."""
    redis_available = app.config.get('REDIS_AVAILABLE', False)
    redis_url = app.config.get('REDIS_URL', '')

    if redis_available and redis_url:
        app.config['RATELIMIT_STORAGE_URL'] = redis_url
    else:
        app.config['RATELIMIT_STORAGE_URL'] = 'memory://'

    try:
        limiter.init_app(app)
        app.logger.info(f"Flask-Limiter usando: {app.config['RATELIMIT_STORAGE_URL']}")
    except Exception as exc:
        app.logger.warning(f"Flask-Limiter falló: {exc}. Reintentando con memory://")
        app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
        try:
            limiter.init_app(app)
        except Exception as exc2:
            app.logger.error(f"Flask-Limiter no pudo inicializarse: {exc2}")


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ProxyFix for Coolify / reverse proxy
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_prefix=1,
    )

    public_dir = os.path.normpath(os.path.join(app.root_path, '..', 'public'))

    @app.route('/public/<path:filename>')
    def backend_public_file(filename):
        return send_from_directory(public_dir, filename)

    # Configure Logging
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(module)s: %(message)s',
            handlers=[logging.StreamHandler()]
        )
    else:
        logging.basicConfig(level=logging.DEBUG)

    # Redis
    init_redis(app)

    # CORS — only for public API, explicit origins
    CORS(
        app,
        resources={
            r"/api/v1/articles": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
            r"/api/v1/articles/*": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
            r"/api/v1/categories": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
            r"/api/v1/tags": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
            r"/api/v1/media/*": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
            r"/api/v1/sitemap": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])},
        },
        methods=["GET", "HEAD", "OPTIONS"],
        supports_credentials=False,
    )

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    ma.init_app(app)

    # Flask-Limiter
    _init_limiter_safe(app)

    # Correlation ID
    @app.before_request
    def attach_request_id():
        g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())

    @app.after_request
    def add_request_id_header(response):
        request_id = getattr(g, 'request_id', None)
        if request_id:
            response.headers['X-Request-ID'] = request_id
        return response

    @app.teardown_request
    def teardown_request(_exc):
        db.session.remove()

    # MinIO
    try:
        minio_service.init_app(app)
    except Exception as exc:
        app.logger.warning(f"MinIO no disponible al iniciar: {exc}")

    # Prometheus
    init_metrics(app)

    # Error Handlers
    register_error_handlers(app)

    # CLI Commands
    app.cli.add_command(create_admin)
    app.cli.add_command(rotate_secret)
    app.cli.add_command(init_bucket)
    app.cli.add_command(import_wiki_data)

    # Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'info'

    # Talisman (Security Headers)
    csp = {
        'default-src': '\'self\'',
        'img-src': ['\'self\'', 'data:', app.config.get('MINIO_PUBLIC_BASE_URL') or '*'],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://cdn.tailwindcss.com',
            'https://cdnjs.cloudflare.com',
            'https://unpkg.com',
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://cdnjs.cloudflare.com',
            'https://fonts.googleapis.com',
            'https://unpkg.com',
        ],
        'font-src': [
            '\'self\'',
            'https://fonts.gstatic.com'
        ]
    }

    force_https = (config_name == 'production')

    talisman.init_app(
        app,
        content_security_policy=csp,
        force_https=force_https,
        frame_options='SAMEORIGIN',
        referrer_policy='strict-origin-when-cross-origin',
    )

    # Register Blueprints
    csrf.exempt(health_bp)
    app.register_blueprint(health_bp)

    # Public API
    from .routes.api import api_bp, admin_api_bp
    csrf.exempt(api_bp)
    csrf.exempt(admin_api_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_api_bp)

    # Admin panel
    from .routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Health checks
    from .health import register_health_routes
    register_health_routes(app)

    # Date Filter
    @app.template_filter('date_es')
    def date_es_filter(dt):
        if not dt:
            return ''
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        return f"{dt.day} de {months[dt.month-1]} de {dt.year}, {dt.strftime('%H:%M')}"

    return app