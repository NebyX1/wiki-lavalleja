"""Service for resolving media://UUID references in markdown."""
import re
from flask import current_app, url_for

MEDIA_REF_PATTERN = re.compile(r'media://([a-f0-9-]{36})')


def resolve_media_urls(markdown_text: str) -> str:
    """Replace media://UUID references with public API URLs."""
    if not markdown_text:
        return markdown_text

    from app.models.media_asset import MediaAsset

    def replacer(match):
        uuid = match.group(1)
        asset = MediaAsset.query.filter_by(uuid=uuid, deleted_at=None).first()
        if asset:
            return f"/api/v1/media/{uuid}/content/large"
        return match.group(0)

    return MEDIA_REF_PATTERN.sub(replacer, markdown_text)