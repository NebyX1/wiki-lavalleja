"""Marshmallow schemas for wiki API (camelCase responses)."""
from marshmallow import fields, validate, validates, ValidationError
from app.extensions import ma
from app.models.article import (
    Article,
    ArticleKeyFact,
    ArticleTimelineEvent,
    ArticleRelatedPlace,
    ArticleSource,
    ArticleRevision,
)
from app.models.category import Category
from app.models.tag import Tag
from app.models.media_asset import MediaAsset


class CategorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Category
        ordered = True

    id = fields.Integer()
    name = fields.String()
    slug = fields.String()
    description = fields.String(allow_none=True)
    sort_order = fields.Integer(data_key="sortOrder")
    is_active = fields.Boolean(data_key="isActive")
    article_count = fields.Method("get_article_count", data_key="articleCount")

    def get_article_count(self, obj):
        return obj.article_count()


class TagSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Tag
        ordered = True

    id = fields.Integer()
    name = fields.String()
    slug = fields.String()


class MediaAssetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MediaAsset
        ordered = True

    id = fields.Integer()
    uuid = fields.String()
    alt_text = fields.String(data_key="altText", allow_none=True)
    caption = fields.String(allow_none=True)
    credit = fields.String(allow_none=True)
    license = fields.String(allow_none=True)
    source_url = fields.String(data_key="sourceUrl", allow_none=True)
    mime_type = fields.String(data_key="mimeType")
    width = fields.Integer(allow_none=True)
    height = fields.Integer(allow_none=True)
    size_bytes = fields.Integer(data_key="sizeBytes")
    created_at = fields.DateTime(data_key="createdAt")
    is_public = fields.Boolean(data_key="isPublic")


class ArticleKeyFactSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleKeyFact
        ordered = True

    id = fields.Integer()
    text = fields.String()
    position = fields.Integer()


class ArticleTimelineEventSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleTimelineEvent
        ordered = True

    id = fields.Integer()
    year = fields.String()
    event = fields.String()
    position = fields.Integer()


class ArticleRelatedPlaceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleRelatedPlace
        ordered = True

    id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True)
    type = fields.String(allow_none=True)
    position = fields.Integer()


class ArticleSourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleSource
        ordered = True

    id = fields.Integer()
    label = fields.String()
    url = fields.String()
    kind = fields.String()
    position = fields.Integer()
    accessed_at = fields.DateTime(data_key="accessedAt", allow_none=True)

    @validates("url")
    def validate_url(self, value, **kwargs):
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https"):
            raise ValidationError("La URL debe usar http o https.")
        if parsed.scheme in ("javascript", "data", "file"):
            raise ValidationError("Esquema de URL no permitido.")


class ArticleRevisionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleRevision
        ordered = True

    id = fields.Integer()
    revision_number = fields.Integer(data_key="revisionNumber")
    created_at = fields.DateTime(data_key="createdAt")
    reason = fields.String(allow_none=True)
    created_by_name = fields.Method("get_created_by_name", data_key="createdByName")

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.username or obj.created_by.email
        return None


class ArticleListSchema(ma.Schema):
    """Lightweight schema for list/card display."""
    id = fields.Integer()
    slug = fields.String()
    title = fields.String()
    subtitle = fields.String(allow_none=True)
    type = fields.String(allow_none=True)
    street_name = fields.String(data_key="streetName", allow_none=True)
    period = fields.String(allow_none=True)
    category = fields.Method("get_category")
    summary = fields.String(allow_none=True)
    hero_image = fields.Method("get_hero_image", data_key="heroImage")
    image_alt = fields.String(data_key="imageAlt", allow_none=True)
    tags = fields.Method("get_tags")
    status = fields.String()
    featured = fields.Boolean()
    published_at = fields.DateTime(data_key="publishedAt", allow_none=True)
    updated_at = fields.DateTime(data_key="updatedAt", allow_none=True)

    def get_category(self, obj):
        if obj.category:
            return {"id": obj.category.id, "name": obj.category.name, "slug": obj.category.slug}
        return None

    def get_tags(self, obj):
        return [{"id": t.id, "name": t.name, "slug": t.slug} for t in obj.tags]

    def get_hero_image(self, obj):
        if obj.hero_media:
            return f"/api/v1/media/{obj.hero_media.uuid}/content/large"
        return None


class ArticleDetailSchema(ma.Schema):
    """Full article schema for detail view."""
    id = fields.Integer()
    slug = fields.String()
    title = fields.String()
    subtitle = fields.String(allow_none=True)
    type = fields.String(allow_none=True)
    street_name = fields.String(data_key="streetName", allow_none=True)
    period = fields.String(allow_none=True)
    birth_place = fields.String(data_key="birthPlace", allow_none=True)
    death_place = fields.String(data_key="deathPlace", allow_none=True)
    category = fields.Method("get_category")
    tags = fields.Method("get_tags")
    summary = fields.String(allow_none=True)
    hero_image = fields.Method("get_hero_image", data_key="heroImage")
    hero_media = fields.Method("get_hero_media", data_key="heroMedia")
    image_alt = fields.String(data_key="imageAlt", allow_none=True)
    image_credit = fields.String(data_key="imageCredit", allow_none=True)
    coordinates = fields.Method("get_coordinates")
    street_evidence = fields.Method("get_street_evidence", data_key="streetEvidence")
    historical_context = fields.String(data_key="historicalContext", allow_none=True)
    key_facts = fields.Method("get_key_facts", data_key="keyFacts")
    timeline = fields.Method("get_timeline")
    related_places = fields.Method("get_related_places", data_key="relatedPlaces")
    sources = fields.Method("get_sources")
    source_notes = fields.String(data_key="sourceNotes", allow_none=True)
    body = fields.Method("get_body")
    status = fields.String()
    featured = fields.Boolean()
    published_at = fields.DateTime(data_key="publishedAt", allow_none=True)
    updated_at = fields.DateTime(data_key="updatedAt", allow_none=True)
    seo = fields.Method("get_seo")

    def get_category(self, obj):
        if obj.category:
            return {"id": obj.category.id, "name": obj.category.name, "slug": obj.category.slug}
        return None

    def get_tags(self, obj):
        return [{"id": t.id, "name": t.name, "slug": t.slug} for t in obj.tags]

    def get_hero_image(self, obj):
        if obj.hero_media:
            return f"/api/v1/media/{obj.hero_media.uuid}/content/large"
        return None

    def get_hero_media(self, obj):
        if obj.hero_media:
            return {
                "id": obj.hero_media.id,
                "uuid": obj.hero_media.uuid,
                "alt": obj.hero_media.alt_text or "",
                "credit": obj.hero_media.credit or "",
                "caption": obj.hero_media.caption or "",
            }
        return None

    def get_coordinates(self, obj):
        if obj.latitude is None and obj.longitude is None:
            return None
        return {
            "lat": obj.latitude,
            "lng": obj.longitude,
            "confidence": obj.coordinate_confidence,
            "note": obj.coordinate_note or "",
        }

    def get_street_evidence(self, obj):
        if not obj.street_evidence_status:
            return None
        return {
            "status": obj.street_evidence_status,
            "note": obj.street_evidence_note or "",
        }

    def get_key_facts(self, obj):
        return [f.text for f in obj.key_facts]

    def get_timeline(self, obj):
        return [{"year": e.year, "event": e.event} for e in obj.timeline_events]

    def get_related_places(self, obj):
        return [{"name": p.name, "description": p.description or "", "type": p.type or ""} for p in obj.related_places]

    def get_sources(self, obj):
        return [{"label": s.label, "url": s.url, "kind": s.kind} for s in obj.sources]

    def get_body(self, obj):
        from app.services.media_resolver import resolve_media_urls
        if obj.body_markdown:
            return resolve_media_urls(obj.body_markdown)
        return None

    def get_seo(self, obj):
        return {
            "title": obj.seo_title or obj.title,
            "description": obj.seo_description or (obj.summary[:160] if obj.summary else None),
            "canonicalUrl": obj.canonical_url,
        }


class ArticleAdminSchema(ma.Schema):
    """Admin schema with all fields for editing."""
    id = fields.Integer(allow_none=True)
    slug = fields.String(required=True)
    title = fields.String(required=True)
    subtitle = fields.String(allow_none=True)
    type = fields.String(allow_none=True)
    street_name = fields.String(data_key="streetName", allow_none=True)
    period = fields.String(allow_none=True)
    birth_place = fields.String(data_key="birthPlace", allow_none=True)
    death_place = fields.String(data_key="deathPlace", allow_none=True)
    category_id = fields.Integer(data_key="categoryId", allow_none=True)
    category = fields.Method("get_category")
    summary = fields.String(allow_none=True)
    hero_media_id = fields.Integer(data_key="heroMediaId", allow_none=True)
    hero_media = fields.Method("get_hero_media", data_key="heroMedia")
    image_alt = fields.String(data_key="imageAlt", allow_none=True)
    image_credit = fields.String(data_key="imageCredit", allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    coordinate_confidence = fields.String(data_key="coordinateConfidence", allow_none=True)
    coordinate_note = fields.String(data_key="coordinateNote", allow_none=True)
    street_evidence_status = fields.String(data_key="streetEvidenceStatus", allow_none=True)
    street_evidence_note = fields.String(data_key="streetEvidenceNote", allow_none=True)
    historical_context = fields.String(data_key="historicalContext", allow_none=True)
    source_notes = fields.String(data_key="sourceNotes", allow_none=True)
    body_markdown = fields.String(data_key="bodyMarkdown", allow_none=True)
    status = fields.String()
    featured = fields.Boolean()
    seo_title = fields.String(data_key="seoTitle", allow_none=True)
    seo_description = fields.String(data_key="seoDescription", allow_none=True)
    canonical_url = fields.String(data_key="canonicalUrl", allow_none=True)
    version = fields.Integer()
    tags = fields.Method("get_tags")
    key_facts = fields.Method("get_key_facts", data_key="keyFacts")
    timeline_events = fields.Method("get_timeline_events", data_key="timeline")
    related_places = fields.Method("get_related_places", data_key="relatedPlaces")
    sources = fields.Method("get_sources")
    created_at = fields.DateTime(data_key="createdAt", allow_none=True)
    updated_at = fields.DateTime(data_key="updatedAt", allow_none=True)
    published_at = fields.DateTime(data_key="publishedAt", allow_none=True)

    def get_category(self, obj):
        if obj.category:
            return {"id": obj.category.id, "name": obj.category.name, "slug": obj.category.slug}
        return None

    def get_tags(self, obj):
        return [{"id": t.id, "name": t.name, "slug": t.slug} for t in obj.tags]

    def get_hero_media(self, obj):
        if obj.hero_media:
            return {
                "id": obj.hero_media.id,
                "uuid": obj.hero_media.uuid,
                "alt": obj.hero_media.alt_text or "",
                "credit": obj.hero_media.credit or "",
            }
        return None

    def get_key_facts(self, obj):
        return [{"id": f.id, "text": f.text, "position": f.position} for f in obj.key_facts]

    def get_timeline_events(self, obj):
        return [{"id": e.id, "year": e.year, "event": e.event, "position": e.position} for e in obj.timeline_events]

    def get_related_places(self, obj):
        return [{"id": p.id, "name": p.name, "description": p.description or "", "type": p.type or "", "position": p.position} for p in obj.related_places]

    def get_sources(self, obj):
        return [{"id": s.id, "label": s.label, "url": s.url, "kind": s.kind, "position": s.position} for s in obj.sources]