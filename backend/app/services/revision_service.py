"""Revision service for article history."""
import json
from app.extensions import db
from app.models.article import ArticleRevision
from app.models.tag import Tag
from app.utils.logging_helper import log_activity


class RevisionService:
    @staticmethod
    def list_revisions(article_id: int):
        return ArticleRevision.query.filter_by(article_id=article_id) \
            .order_by(ArticleRevision.revision_number.desc()).all()

    @staticmethod
    def get_revision(article_id: int, revision_id: int) -> ArticleRevision | None:
        return ArticleRevision.query.filter_by(article_id=article_id, id=revision_id).first()

    @staticmethod
    def restore_revision(article, revision_id: int, user):
        rev = RevisionService.get_revision(article.id, revision_id)
        if not rev:
            return None

        snapshot = json.loads(rev.snapshot_json)

        article.title = snapshot.get("title", article.title)
        article.subtitle = snapshot.get("subtitle")
        article.type = snapshot.get("type")
        article.street_name = snapshot.get("street_name") or snapshot.get("streetName")
        article.period = snapshot.get("period")
        article.birth_place = snapshot.get("birth_place") or snapshot.get("birthPlace")
        article.death_place = snapshot.get("death_place") or snapshot.get("deathPlace")
        article.summary = snapshot.get("summary")
        article.image_alt = snapshot.get("image_alt") or snapshot.get("imageAlt")
        article.image_credit = snapshot.get("image_credit") or snapshot.get("imageCredit")
        article.latitude = snapshot.get("latitude")
        article.longitude = snapshot.get("longitude")
        article.coordinate_confidence = snapshot.get("coordinate_confidence") or snapshot.get("coordinateConfidence")
        article.coordinate_note = snapshot.get("coordinate_note") or snapshot.get("coordinateNote")
        article.street_evidence_status = snapshot.get("street_evidence_status") or snapshot.get("streetEvidenceStatus")
        article.street_evidence_note = snapshot.get("street_evidence_note") or snapshot.get("streetEvidenceNote")
        article.historical_context = snapshot.get("historical_context") or snapshot.get("historicalContext")
        article.source_notes = snapshot.get("source_notes") or snapshot.get("sourceNotes")
        article.body_markdown = snapshot.get("body_markdown") or snapshot.get("bodyMarkdown")
        article.seo_title = snapshot.get("seo_title") or snapshot.get("seoTitle")
        article.seo_description = snapshot.get("seo_description") or snapshot.get("seoDescription")
        article.canonical_url = snapshot.get("canonical_url") or snapshot.get("canonicalUrl")
        article.version += 1
        article.updated_by_id = user.id if user else None

        if snapshot.get("category_id") or snapshot.get("categoryId"):
            article.category_id = snapshot.get("category_id") or snapshot.get("categoryId")

        tags_data = snapshot.get("tags", [])
        article.tags = []
        for t in tags_data:
            slug = t.get("slug", "")
            tag = Tag.query.filter_by(slug=slug).first()
            if tag:
                article.tags.append(tag)

        db.session.commit()
        log_activity(action="ARTICLE_REVISION_RESTORE", details=f"Revisión restaurada: {article.title}", user=user)
        return article