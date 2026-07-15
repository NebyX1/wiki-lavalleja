"""Article service: CRUD, sync children, revisions, concurrency."""
import json
from datetime import datetime
from app.extensions import db
from app.models.article import (
    Article,
    ArticleKeyFact,
    ArticleTimelineEvent,
    ArticleRelatedPlace,
    ArticleSource,
    ArticleRevision,
    ArticleStatus,
)
from app.models.tag import Tag
from app.utils.logging_helper import log_activity


def slugify(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text


import re


class ArticleService:
    @staticmethod
    def create_article(data: dict, user) -> Article:
        article = Article(
            slug=data.get("slug") or slugify(data.get("title", "")),
            title=data["title"],
            subtitle=data.get("subtitle"),
            type=data.get("type"),
            street_name=data.get("streetName"),
            period=data.get("period"),
            birth_place=data.get("birthPlace"),
            death_place=data.get("deathPlace"),
            category_id=data.get("categoryId"),
            summary=data.get("summary"),
            hero_media_id=data.get("heroMediaId"),
            image_alt=data.get("imageAlt"),
            image_credit=data.get("imageCredit"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            coordinate_confidence=data.get("coordinateConfidence"),
            coordinate_note=data.get("coordinateNote"),
            street_evidence_status=data.get("streetEvidenceStatus"),
            street_evidence_note=data.get("streetEvidenceNote"),
            historical_context=data.get("historicalContext"),
            source_notes=data.get("sourceNotes"),
            body_markdown=data.get("bodyMarkdown"),
            status=data.get("status", "draft"),
            featured=data.get("featured", False),
            seo_title=data.get("seoTitle"),
            seo_description=data.get("seoDescription"),
            canonical_url=data.get("canonicalUrl"),
            created_by_id=user.id if user else None,
            updated_by_id=user.id if user else None,
            version=1,
        )
        db.session.add(article)
        db.session.flush()

        ArticleService._sync_tags(article, data.get("tags", []))
        ArticleService._sync_key_facts(article, data.get("keyFacts", []))
        ArticleService._sync_timeline(article, data.get("timeline", []))
        ArticleService._sync_related_places(article, data.get("relatedPlaces", []))
        ArticleService._sync_sources(article, data.get("sources", []))

        db.session.commit()
        log_activity(action="ARTICLE_CREATE", details=f"Artículo creado: {article.title} ({article.slug})", user=user)
        return article

    @staticmethod
    def update_article(article: Article, data: dict, user) -> Article:
        if "version" in data and data["version"] != article.version:
            raise ValueError("CONFLICT: La versión del artículo ha cambiado. Recargá la página.")

        ArticleService._capture_revision(article, user, "Actualización")

        simple_fields = [
            "slug", "title", "subtitle", "type", "streetName", "period",
            "birthPlace", "deathPlace", "summary", "heroMediaId", "imageAlt",
            "imageCredit", "latitude", "longitude", "coordinateConfidence",
            "coordinateNote", "streetEvidenceStatus", "streetEvidenceNote",
            "historicalContext", "sourceNotes", "bodyMarkdown", "featured",
            "seoTitle", "seoDescription", "canonicalUrl",
        ]
        field_map = {
            "streetName": "street_name", "birthPlace": "birth_place", "deathPlace": "death_place",
            "heroMediaId": "hero_media_id", "imageAlt": "image_alt", "imageCredit": "image_credit",
            "coordinateConfidence": "coordinate_confidence", "coordinateNote": "coordinate_note",
            "streetEvidenceStatus": "street_evidence_status", "streetEvidenceNote": "street_evidence_note",
            "historicalContext": "historical_context", "sourceNotes": "source_notes",
            "bodyMarkdown": "body_markdown", "seoTitle": "seo_title", "seoDescription": "seo_description",
            "canonicalUrl": "canonical_url",
        }

        for key in simple_fields:
            if key in data:
                db_field = field_map.get(key, key)
                setattr(article, db_field, data[key])

        if "categoryId" in data:
            article.category_id = data["categoryId"]
        if "status" in data:
            article.status = data["status"]

        article.updated_by_id = user.id if user else None
        article.version += 1

        if "tags" in data:
            ArticleService._sync_tags(article, data["tags"])
        if "keyFacts" in data:
            ArticleService._sync_key_facts(article, data["keyFacts"])
        if "timeline" in data:
            ArticleService._sync_timeline(article, data["timeline"])
        if "relatedPlaces" in data:
            ArticleService._sync_related_places(article, data["relatedPlaces"])
        if "sources" in data:
            ArticleService._sync_sources(article, data["sources"])

        db.session.commit()
        log_activity(action="ARTICLE_UPDATE", details=f"Artículo actualizado: {article.title}", user=user)
        return article

    @staticmethod
    def autosave(article: Article, data: dict, user) -> Article:
        """Lightweight save without creating revisions."""
        simple_fields = [
            "title", "subtitle", "type", "streetName", "period", "birthPlace", "deathPlace",
            "summary", "imageAlt", "imageCredit", "bodyMarkdown", "historicalContext",
            "sourceNotes", "coordinateNote", "streetEvidenceNote",
        ]
        field_map = {
            "streetName": "street_name", "birthPlace": "birth_place", "deathPlace": "death_place",
            "imageAlt": "image_alt", "imageCredit": "image_credit", "bodyMarkdown": "body_markdown",
            "historicalContext": "historical_context", "sourceNotes": "source_notes",
        }

        for key in simple_fields:
            if key in data:
                db_field = field_map.get(key, key)
                setattr(article, db_field, data[key])

        if "latitude" in data:
            article.latitude = data["latitude"]
        if "longitude" in data:
            article.longitude = data["longitude"]
        if "coordinateConfidence" in data:
            article.coordinate_confidence = data["coordinateConfidence"]
        if "streetEvidenceStatus" in data:
            article.street_evidence_status = data["streetEvidenceStatus"]
        if "categoryId" in data:
            article.category_id = data["categoryId"]
        if "featured" in data:
            article.featured = data["featured"]
        if "seoTitle" in data:
            article.seo_title = data["seoTitle"]
        if "seoDescription" in data:
            article.seo_description = data["seoDescription"]
        if "canonicalUrl" in data:
            article.canonical_url = data["canonicalUrl"]
        if "heroMediaId" in data:
            article.hero_media_id = data["heroMediaId"]

        article.updated_by_id = user.id if user else None

        if "tags" in data:
            ArticleService._sync_tags(article, data["tags"])
        if "keyFacts" in data:
            ArticleService._sync_key_facts(article, data["keyFacts"])
        if "timeline" in data:
            ArticleService._sync_timeline(article, data["timeline"])
        if "relatedPlaces" in data:
            ArticleService._sync_related_places(article, data["relatedPlaces"])
        if "sources" in data:
            ArticleService._sync_sources(article, data["sources"])

        db.session.commit()
        log_activity(action="ARTICLE_AUTOSAVE", details=f"Autoguardado: {article.title}", user=user)
        return article

    @staticmethod
    def _sync_tags(article: Article, tags_data: list):
        article.tags = []
        for t in tags_data:
            if isinstance(t, dict):
                tag_name = t.get("name", "")
            else:
                tag_name = str(t)
            if not tag_name:
                continue
            slug = slugify(tag_name)
            tag = Tag.query.filter_by(slug=slug).first()
            if not tag:
                tag = Tag(name=tag_name, slug=slug)
                db.session.add(tag)
                db.session.flush()
            article.tags.append(tag)

    @staticmethod
    def _sync_key_facts(article: Article, facts_data: list):
        ArticleKeyFact.query.filter_by(article_id=article.id).delete()
        for i, f in enumerate(facts_data):
            text = f.get("text", "") if isinstance(f, dict) else str(f)
            if text:
                db.session.add(ArticleKeyFact(
                    article_id=article.id, text=text,
                    position=f.get("position", i) if isinstance(f, dict) else i,
                ))

    @staticmethod
    def _sync_timeline(article: Article, timeline_data: list):
        ArticleTimelineEvent.query.filter_by(article_id=article.id).delete()
        for i, e in enumerate(timeline_data):
            year = e.get("year", "") if isinstance(e, dict) else ""
            event = e.get("event", "") if isinstance(e, dict) else str(e)
            if year or event:
                db.session.add(ArticleTimelineEvent(
                    article_id=article.id, year=year, event=event,
                    position=e.get("position", i) if isinstance(e, dict) else i,
                ))

    @staticmethod
    def _sync_related_places(article: Article, places_data: list):
        ArticleRelatedPlace.query.filter_by(article_id=article.id).delete()
        for i, p in enumerate(places_data):
            if isinstance(p, dict):
                db.session.add(ArticleRelatedPlace(
                    article_id=article.id,
                    name=p.get("name", ""),
                    description=p.get("description", ""),
                    type=p.get("type", ""),
                    position=p.get("position", i),
                ))

    @staticmethod
    def _sync_sources(article: Article, sources_data: list):
        ArticleSource.query.filter_by(article_id=article.id).delete()
        for i, s in enumerate(sources_data):
            if isinstance(s, dict):
                label = s.get("label", "")
                url = s.get("url", "")
                kind = s.get("kind", "referencia")
                if label and url:
                    db.session.add(ArticleSource(
                        article_id=article.id, label=label, url=url, kind=kind,
                        position=s.get("position", i),
                    ))

    @staticmethod
    def _capture_revision(article: Article, user, reason: str):
        from app.schemas.wiki_schemas import ArticleAdminSchema
        schema = ArticleAdminSchema()
        snapshot = schema.dump(article)
        latest_rev = ArticleRevision.query.filter_by(article_id=article.id) \
            .order_by(ArticleRevision.revision_number.desc()).first()
        next_num = (latest_rev.revision_number + 1) if latest_rev else 1
        rev = ArticleRevision(
            article_id=article.id,
            revision_number=next_num,
            snapshot_json=json.dumps(snapshot, default=str),
            created_by_id=user.id if user else None,
            reason=reason,
        )
        db.session.add(rev)
        db.session.flush()

    @staticmethod
    def soft_delete(article: Article, user):
        article.deleted_at = datetime.utcnow()
        article.status = "archived"
        db.session.commit()
        log_activity(action="ARTICLE_DELETE", details=f"Artículo borrado (soft): {article.title}", user=user)

    @staticmethod
    def hard_delete(article: Article, user):
        title = article.title
        db.session.delete(article)
        db.session.commit()
        log_activity(action="ARTICLE_PURGE", details=f"Artículo eliminado físicamente: {title}", user=user)

    @staticmethod
    def archive(article: Article, user):
        article.status = ArticleStatus.ARCHIVED.value
        article.archived_at = datetime.utcnow()
        db.session.commit()
        log_activity(action="ARTICLE_ARCHIVE", details=f"Artículo archivado: {article.title}", user=user)

    @staticmethod
    def restore(article: Article, user):
        article.deleted_at = None
        article.archived_at = None
        if article.status == "archived":
            article.status = "draft"
        db.session.commit()
        log_activity(action="ARTICLE_RESTORE", details=f"Artículo restaurado: {article.title}", user=user)

    @staticmethod
    def duplicate(article: Article, user):
        new_slug = f"{article.slug}-copia"
        base_slug = new_slug
        counter = 1
        while Article.query.filter_by(slug=new_slug).first():
            new_slug = f"{base_slug}-{counter}"
            counter += 1

        new_article = Article(
            slug=new_slug,
            title=f"{article.title} (copia)",
            subtitle=article.subtitle,
            type=article.type,
            street_name=article.street_name,
            period=article.period,
            birth_place=article.birth_place,
            death_place=article.death_place,
            category_id=article.category_id,
            summary=article.summary,
            hero_media_id=article.hero_media_id,
            image_alt=article.image_alt,
            image_credit=article.image_credit,
            latitude=article.latitude,
            longitude=article.longitude,
            coordinate_confidence=article.coordinate_confidence,
            coordinate_note=article.coordinate_note,
            street_evidence_status=article.street_evidence_status,
            street_evidence_note=article.street_evidence_note,
            historical_context=article.historical_context,
            source_notes=article.source_notes,
            body_markdown=article.body_markdown,
            status="draft",
            featured=False,
            seo_title=article.seo_title,
            seo_description=article.seo_description,
            canonical_url=None,
            created_by_id=user.id if user else None,
            updated_by_id=user.id if user else None,
            version=1,
        )
        db.session.add(new_article)
        db.session.flush()

        new_article.tags = list(article.tags)

        for f in article.key_facts:
            db.session.add(ArticleKeyFact(article_id=new_article.id, text=f.text, position=f.position))
        for e in article.timeline_events:
            db.session.add(ArticleTimelineEvent(article_id=new_article.id, year=e.year, event=e.event, position=e.position))
        for p in article.related_places:
            db.session.add(ArticleRelatedPlace(article_id=new_article.id, name=p.name, description=p.description, type=p.type, position=p.position))
        for s in article.sources:
            db.session.add(ArticleSource(article_id=new_article.id, label=s.label, url=s.url, kind=s.kind, position=s.position))

        db.session.commit()
        log_activity(action="ARTICLE_DUPLICATE", details=f"Artículo duplicado: {article.title} → {new_article.title}", user=user)
        return new_article