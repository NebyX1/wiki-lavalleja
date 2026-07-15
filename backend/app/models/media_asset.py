"""MediaAsset model for wiki image library."""
from datetime import datetime
from app.extensions import db


class MediaAsset(db.Model):
    __tablename__ = "media_assets"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, index=True, nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    object_name = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    extension = db.Column(db.String(10), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    checksum_sha256 = db.Column(db.String(64), index=True, nullable=True)

    # Variants
    small_object = db.Column(db.String(500), nullable=True)
    medium_object = db.Column(db.String(500), nullable=True)
    large_object = db.Column(db.String(500), nullable=True)
    original_object = db.Column(db.String(500), nullable=True)
    small_width = db.Column(db.Integer, nullable=True)
    small_height = db.Column(db.Integer, nullable=True)
    medium_width = db.Column(db.Integer, nullable=True)
    medium_height = db.Column(db.Integer, nullable=True)
    large_width = db.Column(db.Integer, nullable=True)
    large_height = db.Column(db.Integer, nullable=True)

    # Metadata
    alt_text = db.Column(db.String(500), nullable=True)
    caption = db.Column(db.String(500), nullable=True)
    credit = db.Column(db.String(255), nullable=True)
    license = db.Column(db.String(100), nullable=True)
    source_url = db.Column(db.String(500), nullable=True)
    is_public = db.Column(db.Boolean, default=True, nullable=False)

    users_with_access = db.Column(db.String(255), nullable=True)

    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    uploaded_by = db.relationship("User", backref="uploaded_media")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<MediaAsset {self.uuid}>"

    @property
    def is_deleted(self):
        return self.deleted_at is not None