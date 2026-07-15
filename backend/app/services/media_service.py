"""Media service for image upload, processing, and MinIO storage."""
import io
import uuid
import hashlib
from datetime import datetime
from flask import current_app, url_for
from PIL import Image, ImageOps
from app.extensions import db
from app.models.media_asset import MediaAsset
from app.services.minio_service import minio_service
from app.utils.logging_helper import log_activity

ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


class MediaService:
    @staticmethod
    def _generate_uuid():
        return str(uuid.uuid4())

    @staticmethod
    def _get_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _detect_mime(file_storage) -> str | None:
        file_storage.seek(0)
        header = file_storage.read(512)
        file_storage.seek(0)
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if header[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return "image/webp"
        return file_storage.content_type

    @staticmethod
    def _detect_extension(mime: str) -> str:
        return {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(mime, "bin")

    @staticmethod
    def _process_image(img: Image.Image, max_width: int) -> tuple[bytes, int, int]:
        if img.mode in ("RGBA", "P"):
            pass
        else:
            img = img.convert("RGB")

        img = ImageOps.exif_transpose(img)

        original_w, original_h = img.size
        if original_w > max_width:
            ratio = max_width / original_w
            new_w = max_width
            new_h = int(original_h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img.save(buf, format="WEBP", quality=85, lossless=False)
        else:
            img.save(buf, format="WEBP", quality=85)
        return buf.getvalue(), img.size[0], img.size[1]

    @staticmethod
    def upload(file_storage, user, alt_text=None, caption=None, credit=None, license=None, source_url=None):
        mime = MediaService._detect_mime(file_storage)
        if mime not in ALLOWED_MIMES:
            raise ValueError(f"Tipo de archivo no permitido: {mime}. Solo se aceptan JPEG, PNG y WebP.")

        file_storage.seek(0)
        try:
            img = Image.open(file_storage)
        except Exception:
            raise ValueError("Archivo de imagen corrupto o no válido.")

        file_storage.seek(0)
        original_data = file_storage.read()
        max_size = current_app.config.get("WIKI_MEDIA_MAX_BYTES", 10 * 1024 * 1024)
        if len(original_data) > max_size:
            raise ValueError(f"Archivo demasiado grande. Máximo: {max_size // (1024*1024)} MB.")

        max_dim = current_app.config.get("WIKI_MEDIA_MAX_WIDTH", 12000)
        if img.width > max_dim or img.height > max_dim:
            raise ValueError(f"Dimensiones excesivas. Máximo: {max_dim}px por lado.")

        media_uuid = MediaService._generate_uuid()
        now = datetime.utcnow()
        date_prefix = f"wiki-media/{now.strftime('%Y/%m')}/{media_uuid}"

        checksum = MediaService._get_sha256(original_data)
        ext = MediaService._detect_extension(mime)

        small_data, sw, sh = MediaService._process_image(img, current_app.config.get("WIKI_MEDIA_SMALL_WIDTH", 480))
        medium_data, mw, mh = MediaService._process_image(img, current_app.config.get("WIKI_MEDIA_MEDIUM_WIDTH", 960))
        large_data, lw, lh = MediaService._process_image(img, current_app.config.get("WIKI_MEDIA_LARGE_WIDTH", 1600))

        original_obj = f"{date_prefix}/original.{ext}"
        small_obj = f"{date_prefix}/small.webp"
        medium_obj = f"{date_prefix}/medium.webp"
        large_obj = f"{date_prefix}/large.webp"

        for obj_name, data in [
            (original_obj, original_data),
            (small_obj, small_data),
            (medium_obj, medium_data),
            (large_obj, large_data),
        ]:
            minio_service.client.put_object(
                minio_service.bucket_name,
                obj_name,
                io.BytesIO(data),
                len(data),
                content_type="image/webp" if obj_name != original_obj else mime,
            )

        original_ext = MediaService._detect_extension(mime)

        asset = MediaAsset(
            uuid=media_uuid,
            original_filename=file_storage.filename or "upload",
            object_name=original_obj,
            mime_type=mime,
            extension=original_ext,
            size_bytes=len(original_data),
            width=img.width,
            height=img.height,
            checksum_sha256=checksum,
            original_object=original_obj,
            small_object=small_obj,
            medium_object=medium_obj,
            large_object=large_obj,
            small_width=sw,
            small_height=sh,
            medium_width=mw,
            medium_height=mh,
            large_width=lw,
            large_height=lh,
            alt_text=alt_text,
            caption=caption,
            credit=credit,
            license=license,
            source_url=source_url,
            is_public=True,
            uploaded_by_id=user.id if user else None,
        )
        db.session.add(asset)
        db.session.commit()
        log_activity(action="MEDIA_UPLOAD", details=f"Imagen subida: {asset.uuid}", user=user)
        return asset

    @staticmethod
    def get_by_uuid(media_uuid: str) -> MediaAsset | None:
        return MediaAsset.query.filter_by(uuid=media_uuid, deleted_at=None).first()

    @staticmethod
    def list_media(q=None, page=1, per_page=24):
        query = MediaAsset.query.filter(MediaAsset.deleted_at.is_(None))
        if q:
            query = query.filter(
                db.or_(
                    MediaAsset.original_filename.ilike(f"%{q}%"),
                    MediaAsset.alt_text.ilike(f"%{q}%"),
                    MediaAsset.credit.ilike(f"%{q}%"),
                )
            )
        query = query.order_by(MediaAsset.created_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def update_metadata(asset: MediaAsset, data: dict, user):
        if "altText" in data:
            asset.alt_text = data["altText"]
        if "caption" in data:
            asset.caption = data["caption"]
        if "credit" in data:
            asset.credit = data["credit"]
        if "license" in data:
            asset.license = data["license"]
        if "sourceUrl" in data:
            asset.source_url = data["sourceUrl"]
        db.session.commit()
        log_activity(action="MEDIA_UPDATE", details=f"Metadatos actualizados: {asset.uuid}", user=user)
        return asset

    @staticmethod
    def check_usage(media_uuid: str) -> list[dict]:
        asset = MediaService.get_by_uuid(media_uuid)
        if not asset:
            return []

        from app.models.article import Article
        usage = []

        articles_with_hero = Article.query.filter_by(hero_media_id=asset.id, deleted_at=None).all()
        for a in articles_with_hero:
            usage.append({"type": "hero", "article_id": a.id, "article_title": a.title, "article_slug": a.slug})

        articles = Article.query.filter(Article.deleted_at.is_(None), Article.body_markdown.isnot(None)).all()
        for a in articles:
            if f"media://{media_uuid}" in (a.body_markdown or ""):
                usage.append({"type": "embedded", "article_id": a.id, "article_title": a.title, "article_slug": a.slug})

        return usage

    @staticmethod
    def soft_delete(asset: MediaAsset, user):
        usage = MediaService.check_usage(asset.uuid)
        if usage:
            raise ValueError("La imagen está en uso y no puede eliminarse.")

        asset.deleted_at = datetime.utcnow()
        db.session.commit()
        log_activity(action="MEDIA_DELETE", details=f"Imagen eliminada: {asset.uuid}", user=user)

    @staticmethod
    def get_variant_object(asset: MediaAsset, variant: str) -> str | None:
        variant_map = {
            "small": asset.small_object,
            "medium": asset.medium_object,
            "large": asset.large_object,
            "original": asset.original_object,
        }
        return variant_map.get(variant)

    @staticmethod
    def get_media_content(asset: MediaAsset, variant: str) -> tuple[bytes, str] | None:
        obj_name = MediaService.get_variant_object(asset, variant)
        if not obj_name:
            return None

        content = minio_service.get_file_content(obj_name)
        if content is None:
            return None

        content_type = "image/webp" if variant != "original" else asset.mime_type
        return content, content_type