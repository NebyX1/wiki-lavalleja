from flask import Blueprint, jsonify, current_app
from app.extensions import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health/live', methods=['GET'])
def health_live():
    """Liveness probe — process is running."""
    return jsonify({'status': 'alive'}), 200


@health_bp.route('/health', methods=['GET'])
def health():
    """Legacy health endpoint."""
    return jsonify({'status': 'ok'}), 200


def register_health_routes(app):
    @app.route('/health/ready', methods=['GET'])
    def health_ready():
        """Readiness probe — check deps."""
        checks = {'status': 'ready', 'checks': {}}

        # Database
        try:
            db.session.execute(db.text('SELECT 1'))
            checks['checks']['database'] = 'ok'
        except Exception as e:
            checks['checks']['database'] = f'error: {e}'
            checks['status'] = 'not_ready'

        # Redis
        if app.config.get('REDIS_AVAILABLE'):
            checks['checks']['redis'] = 'ok'
        elif app.config.get('REQUIRE_REDIS_IN_PRODUCTION') and app.config.get('FLASK_CONFIG') == 'production':
            checks['checks']['redis'] = 'required but unavailable'
            checks['status'] = 'not_ready'
        else:
            checks['checks']['redis'] = 'optional, not configured'

        # MinIO
        from app.services.minio_service import minio_service
        if minio_service.client:
            checks['checks']['minio'] = 'ok'
        elif app.config.get('REQUIRE_MINIO_IN_PRODUCTION') and app.config.get('FLASK_CONFIG') == 'production':
            checks['checks']['minio'] = 'required but unavailable'
            checks['status'] = 'not_ready'
        else:
            checks['checks']['minio'] = 'optional, not configured'

        status_code = 200 if checks['status'] == 'ready' else 503
        return jsonify(checks), status_code