from flask import jsonify, render_template, request, g
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(e):
        return _format_error(e, 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return _format_error(e, 401)

    @app.errorhandler(403)
    def forbidden(e):
        return _format_error(e, 403)

    @app.errorhandler(404)
    def page_not_found(e):
        return _format_error(e, 404)

    @app.errorhandler(409)
    def conflict(e):
        return _format_error(e, 409)

    @app.errorhandler(413)
    def payload_too_large(e):
        return _format_error(e, 413, message="Archivo demasiado grande.")

    @app.errorhandler(415)
    def unsupported_media(e):
        return _format_error(e, 415, message="Tipo de medio no soportado.")

    @app.errorhandler(422)
    def unprocessable(e):
        return _format_error(e, 422)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return _format_error(e, 429, message="Límite de peticiones excedido. Intente nuevamente más tarde.")

    @app.errorhandler(500)
    def internal_server_error(e):
        return _format_error(e, 500, message="Ocurrió un error interno del servidor.")


def _format_error(e, status_code, message=None):
    if not message:
        if status_code == 404:
            message = "Página no encontrada."
        elif status_code == 403:
            message = "Acceso denegado."
        elif status_code == 401:
            message = "No autorizado."
        else:
            message = getattr(e, 'description', str(e))

    if current_is_json():
        error_codes = {
            400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
            404: "NOT_FOUND", 409: "CONFLICT", 413: "PAYLOAD_TOO_LARGE",
            415: "UNSUPPORTED_MEDIA_TYPE", 422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMITED", 500: "INTERNAL_ERROR",
        }
        return jsonify({
            "error": {
                "code": error_codes.get(status_code, "ERROR"),
                "message": message,
                "details": None,
                "requestId": getattr(g, "request_id", None),
            }
        }), status_code

    return render_template('errors.html', error=e, code=status_code, message=message), status_code


def current_is_json():
    return request.is_json or request.path.startswith('/api/')