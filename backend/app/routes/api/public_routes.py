from flask import Blueprint, jsonify, request, Response, abort, current_app
from app.services.article_query_service import ArticleQueryService
from app.services.media_service import MediaService
from app.services.taxonomy_service import CategoryService, TagService
from app.schemas.wiki_schemas import (
    ArticleListSchema,
    ArticleDetailSchema,
    CategorySchema,
    TagSchema,
    MediaAssetSchema,
)

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


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


@api_bp.route("/articles", methods=["GET"])
def list_articles():
    q = request.args.get("q", "").strip() or None
    category = request.args.get("category") or None
    article_type = request.args.get("type") or None
    tag = request.args.get("tag") or None
    featured = request.args.get("featured")
    if featured is not None:
        featured = featured.lower() in ("true", "1", "yes")
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("perPage", 12, type=int), 1), 50)
    sort = request.args.get("sort", "newest")
    if sort not in ("newest", "oldest", "title", "updated"):
        sort = "newest"

    pagination = ArticleQueryService.list_public(
        q=q, category=category, article_type=article_type, tag=tag,
        featured=featured, page=page, per_page=per_page, sort=sort,
    )

    schema = ArticleListSchema(many=True)
    items = schema.dump(pagination.items)

    return jsonify({
        "items": items,
        "pagination": {
            "page": pagination.page,
            "perPage": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "hasNext": pagination.has_next,
            "hasPrevious": pagination.has_prev,
        }
    })


@api_bp.route("/articles/<slug>", methods=["GET"])
def get_article(slug):
    article = ArticleQueryService.get_by_slug(slug)
    if not article or not article.is_published:
        return _error_response("ARTICLE_NOT_FOUND", "Artículo no encontrado.", 404)

    schema = ArticleDetailSchema()
    return jsonify(schema.dump(article))


@api_bp.route("/categories", methods=["GET"])
def list_categories():
    categories = ArticleQueryService.get_published_categories()
    schema = CategorySchema(many=True)
    return jsonify(schema.dump(categories))


@api_bp.route("/tags", methods=["GET"])
def list_tags():
    tag_data = ArticleQueryService.get_published_tags()
    result = [{"id": t.id, "name": t.name, "slug": t.slug, "articleCount": count} for t, count in tag_data]
    return jsonify(result)


@api_bp.route("/media/<uuid>/content/<variant>", methods=["GET"])
def get_media_content(uuid, variant):
    if variant not in ("small", "medium", "large", "original"):
        return _error_response("INVALID_VARIANT", "Variante no válida.", 400)

    asset = MediaService.get_by_uuid(uuid)
    if not asset or not asset.is_public:
        return _error_response("MEDIA_NOT_FOUND", "Imagen no encontrada.", 404)

    result = MediaService.get_media_content(asset, variant)
    if result is None:
        return _error_response("MEDIA_NOT_FOUND", "Contenido no disponible.", 404)

    content, content_type = result
    response = Response(content, mimetype=content_type)
    response.headers["Cache-Control"] = "public, max-age=86400"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@api_bp.route("/sitemap", methods=["GET"])
def sitemap():
    from flask import url_for
    articles = Article.query.filter_by(status="published", deleted_at=None).all()
    base_url = current_app.config.get("APP_BASE_URL", "").rstrip("/")

    urls = []
    if base_url:
        urls.append(f"{base_url}/")
        for a in articles:
            urls.append(f"{base_url}/articulos/{a.slug}")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url><loc>{url}</loc></url>\n"
    xml += "</urlset>"

    return Response(xml, mimetype="application/xml")