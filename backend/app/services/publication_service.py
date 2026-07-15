"""Publication service for article status transitions."""
from datetime import datetime
from app.extensions import db
from app.models.article import Article
from app.utils.logging_helper import log_activity


class PublicationService:
    @staticmethod
    def publish(article: Article, user) -> tuple[bool, list[str]]:
        is_valid, errors = article.validate_for_publish()
        if not is_valid:
            return False, errors

        article.status = "published"
        article.published_at = datetime.utcnow()
        article.published_by_id = user.id if user else None
        article.archived_at = None
        db.session.commit()
        log_activity(action="ARTICLE_PUBLISH", details=f"Artículo publicado: {article.title}", user=user)
        return True, []

    @staticmethod
    def unpublish(article: Article, user):
        article.status = "draft"
        db.session.commit()
        log_activity(action="ARTICLE_UNPUBLISH", details=f"Artículo retirado de publicación: {article.title}", user=user)

    @staticmethod
    def submit_review(article: Article, user):
        article.status = "review"
        db.session.commit()
        log_activity(action="ARTICLE_SUBMIT_REVIEW", details=f"Artículo enviado a revisión: {article.title}", user=user)