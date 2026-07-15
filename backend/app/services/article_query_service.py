"""Query service for article listings and lookups."""
from app.extensions import db
from app.models.article import Article, ArticleStatus
from app.models.category import Category
from app.models.tag import Tag


class ArticleQueryService:
    @staticmethod
    def list_public(q=None, category=None, article_type=None, tag=None,
                    featured=None, page=1, per_page=12, sort="newest"):
        query = Article.query.filter_by(status="published", deleted_at=None)

        if q:
            search = f"%{q.lower()}%"
            query = query.filter(
                db.or_(
                    Article.title.ilike(f"%{q}%"),
                    Article.subtitle.ilike(f"%{q}%"),
                    Article.summary.ilike(f"%{q}%"),
                    Article.street_name.ilike(f"%{q}%"),
                    Article.type.ilike(f"%{q}%"),
                )
            )

        if category:
            cat = Category.query.filter_by(slug=category, is_active=True).first()
            if cat:
                query = query.filter(Article.category_id == cat.id)
            else:
                query = query.filter(False)

        if article_type:
            query = query.filter(Article.type == article_type)

        if tag:
            tag_obj = Tag.query.filter_by(slug=tag).first()
            if tag_obj:
                query = query.filter(Article.tags.contains(tag_obj))

        if featured is not None:
            query = query.filter(Article.featured == featured)

        if sort == "oldest":
            query = query.order_by(Article.published_at.asc())
        elif sort == "title":
            query = query.order_by(Article.title.asc())
        elif sort == "updated":
            query = query.order_by(Article.updated_at.desc())
        else:
            query = query.order_by(Article.published_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination

    @staticmethod
    def get_by_slug(slug: str) -> Article | None:
        return Article.query.filter_by(slug=slug, deleted_at=None).first()

    @staticmethod
    def get_by_id(article_id: int) -> Article | None:
        return Article.query.get(article_id)

    @staticmethod
    def list_admin(q=None, status=None, category=None, page=1, per_page=20):
        query = Article.query.filter(Article.deleted_at.is_(None))

        if q:
            query = query.filter(Article.title.ilike(f"%{q}%"))
        if status:
            query = query.filter(Article.status == status)
        if category:
            cat = Category.query.filter_by(slug=category).first()
            if cat:
                query = query.filter(Article.category_id == cat.id)

        query = query.order_by(Article.updated_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination

    @staticmethod
    def get_published_categories():
        return Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()

    @staticmethod
    def get_published_tags():
        tags = Tag.query.all()
        result = []
        for t in tags:
            count = Article.query.filter(
                Article.tags.contains(t),
                Article.status == "published",
                Article.deleted_at.is_(None),
            ).count()
            if count > 0:
                result.append((t, count))
        return result