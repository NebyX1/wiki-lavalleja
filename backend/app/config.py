import os
from dotenv import load_dotenv
from .redis_utils import build_redis_url_from_env

load_dotenv()


def _parse_list_from_env(name: str) -> list[str]:
    raw = os.environ.get(name)
    if raw:
        return [item.strip() for item in raw.split(',') if item.strip()]
    return []


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or SECRET_KEY

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _is_sqlite = bool(
        SQLALCHEMY_DATABASE_URI
        and SQLALCHEMY_DATABASE_URI.startswith('sqlite')
    )
    if _is_sqlite:
        SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '1800')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
        }

    # Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ('true', '1', 't')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # MinIO
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'True').lower() in ('true', '1', 't')
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET_NAME') or os.environ.get('MINIO_BUCKET')
    MINIO_PUBLIC_BASE_URL = os.environ.get('MINIO_PUBLIC_BASE_URL') or os.environ.get('MINIO_PUBLIC_URL')
    MINIO_PRESIGNED_EXPIRY = int(os.environ.get('MINIO_PRESIGNED_EXPIRY', '3600'))

    # Redis
    REDIS_URL = build_redis_url_from_env(os.environ)
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

    # CORS
    CORS_ALLOWED_ORIGINS = _parse_list_from_env('CORS_ORIGINS') or [
        os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    ]

    # URLs
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
    APP_BASE_URL = os.environ.get('APP_BASE_URL', 'http://localhost:5000')
    PUBLIC_SITE_URL = os.environ.get('PUBLIC_SITE_URL', FRONTEND_URL)

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB for media uploads
    SESSION_LIFETIME_MINUTES = int(os.environ.get('SESSION_LIFETIME_MINUTES', '480'))  # 8 hours

    # Content upload limits
    WIKI_MEDIA_MAX_BYTES = int(os.environ.get('WIKI_MEDIA_MAX_BYTES', str(10 * 1024 * 1024)))
    WIKI_MEDIA_MAX_WIDTH = int(os.environ.get('WIKI_MEDIA_MAX_WIDTH', '12000'))
    WIKI_MEDIA_MAX_HEIGHT = int(os.environ.get('WIKI_MEDIA_MAX_HEIGHT', '12000'))
    WIKI_MEDIA_WEBP_QUALITY = int(os.environ.get('WIKI_MEDIA_WEBP_QUALITY', '85'))
    WIKI_MEDIA_SMALL_WIDTH = int(os.environ.get('WIKI_MEDIA_SMALL_WIDTH', '480'))
    WIKI_MEDIA_MEDIUM_WIDTH = int(os.environ.get('WIKI_MEDIA_MEDIUM_WIDTH', '960'))
    WIKI_MEDIA_LARGE_WIDTH = int(os.environ.get('WIKI_MEDIA_LARGE_WIDTH', '1600'))

    # 2FA
    ENABLE_2FA_CODE_LOGGING = os.environ.get('ENABLE_2FA_CODE_LOGGING', 'False').lower() in ('true', '1', 't')
    MAX_2FA_ATTEMPTS = int(os.environ.get('MAX_2FA_ATTEMPTS', '5'))

    # OpenAPI
    OPENAPI_ENABLED = os.environ.get('OPENAPI_ENABLED', 'True').lower() in ('true', '1', 't')

    # Required services in production
    REQUIRE_REDIS_IN_PRODUCTION = os.environ.get('REQUIRE_REDIS_IN_PRODUCTION', 'False').lower() in ('true', '1', 't')
    REQUIRE_MINIO_IN_PRODUCTION = os.environ.get('REQUIRE_MINIO_IN_PRODUCTION', 'False').lower() in ('true', '1', 't')

    # Logging
    LOG_FORMAT = os.environ.get('LOG_FORMAT', '%(asctime)s [%(levelname)s] %(module)s: %(message)s')


class DevelopmentConfig(Config):
    DEBUG = True
    RATELIMIT_STORAGE_URL = "memory://"
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}