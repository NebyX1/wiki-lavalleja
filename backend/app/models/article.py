"""Article model for wiki content."""
from datetime import datetime
import enum
from app.extensions import db


class ArticleStatus(enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    @classmethod
    def values(cls):
        return [s.value for s in cls]


article_tags = db.Table(
    "article_tags",
    db.Column("article_id", db.Integer, db.ForeignKey("articles.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Article(db.Model):
    """Article for WikiLavalleja encyclopedia."""
    __tablename__ = "articles"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(200), unique=True, index=True, nullable=False)
    title = db.Column(db.String(300), nullable=False)
    subtitle = db.Column(db.String(500), nullable=True)
    type = db.Column(db.String(100), nullable=True)
    street_name = db.Column(db.String(200), nullable=True)
    period = db.Column(db.String(100), nullable=True)
    birth_place = db.Column(db.String(200), nullable=True)
    death_place = db.Column(db.String(200), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True, index=True)

    summary = db.Column(db.Text, nullable=True)

    hero_media_id = db.Column(db.Integer, db.ForeignKey("media_assets.id"), nullable=True)
    hero_media = db.relationship("MediaAsset", foreign_keys=[hero_media_id])

    image_alt = db.Column(db.String(500), nullable=True)
    image_credit = db.Column(db.String(500), nullable=True)

    # Coordinates
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    coordinate_confidence = db.Column(db.String(20), nullable=True)
    coordinate_note = db.Column(db.Text, nullable=True)

    # Street evidence
    street_evidence_status = db.Column(db.String(20), nullable=True)
    street_evidence_note = db.Column(db.Text, nullable=True)

    historical_context = db.Column(db.Text, nullable=True)
    source_notes = db.Column(db.Text, nullable=True)
    body_markdown = db.Column(db.Text, nullable=True)

    # Editorial status
    status = db.Column(db.String(20), default="draft", nullable=False, index=True)
    featured = db.Column(db.Boolean, default=False, nullable=False, index=True)

    # SEO
    seo_title = db.Column(db.String(200), nullable=True)
    seo_description = db.Column(db.String(300), nullable=True)
    canonical_url = db.Column(db.String(500), nullable=True)

    # Authors
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    published_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id], backref="articles_created")
    updated_by = db.relationship("User", foreign_keys=[updated_by_id])
    published_by = db.relationship("User", foreign_keys=[published_by_id])

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    published_at = db.Column(db.DateTime, nullable=True, index=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)

    # Concurrency control
    version = db.Column(db.Integer, default=1, nullable=False)

    # Relationships
    tags = db.relationship("Tag", secondary=article_tags, backref="articles")
    key_facts = db.relationship("ArticleKeyFact", backref="article", cascade="all, delete-orphan", order_by="ArticleKeyFact.position", lazy=True)
    timeline_events = db.relationship("ArticleTimelineEvent", backref="article", cascade="all, delete-orphan", order_by="ArticleTimelineEvent.position", lazy=True)
    related_places = db.relationship("ArticleRelatedPlace", backref="article", cascade="all, delete-orphan", order_by="ArticleRelatedPlace.position", lazy=True)
    sources = db.relationship("ArticleSource", backref="article", cascade="all, delete-orphan", order_by="ArticleSource.position", lazy=True)
    revisions = db.relationship("ArticleRevision", backref="article", cascade="all, delete-orphan", order_by="ArticleRevision.revision_number.desc()", lazy=True)

    def __repr__(self):
        return f"<Article {self.slug}>"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def is_published(self):
        return self.status == "published" and self.deleted_at is None and self.published_at is not None

    def validate_for_publish(self):
        """Returns (is_valid, list_of_errors)."""
        errors = []
        if not self.title:
            errors.append("El título es obligatorio.")
        if not self.summary:
            errors.append("El resumen es obligatorio.")
        if not self.body_markdown:
            errors.append("El cuerpo del artículo es obligatorio.")
        if not self.category_id:
            errors.append("La categoría es obligatoria.")
        if not self.sources or len(self.sources) == 0:
            errors.append("Al menos una fuente es obligatoria.")
        if self.hero_media_id and not self.image_alt:
            errors.append("La imagen principal debe tener texto alternativo.")
        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            errors.append("La latitud debe estar entre -90 y 90.")
        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            errors.append("La longitud debe estar entre -180 y 180.")
        return len(errors) == 0, errors


class ArticleKeyFact(db.Model):
    __tablename__ = "article_key_facts"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)


class ArticleTimelineEvent(db.Model):
    __tablename__ = "article_timeline_events"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    year = db.Column(db.String(50), nullable=False)
    event = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)


class ArticleRelatedPlace(db.Model):
    __tablename__ = "article_related_places"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.String(100), nullable=True)
    position = db.Column(db.Integer, default=0, nullable=False)


class ArticleSource(db.Model):
    __tablename__ = "article_sources"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    label = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    kind = db.Column(db.String(20), nullable=False)
    position = db.Column(db.Integer, default=0, nullable=False)
    accessed_at = db.Column(db.DateTime, nullable=True)


class ArticleRevision(db.Model):
    __tablename__ = "article_revisions"

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("articles.id"), nullable=False, index=True)
    revision_number = db.Column(db.Integer, nullable=False)
    snapshot_json = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.relationship("User")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(200), nullable=True)