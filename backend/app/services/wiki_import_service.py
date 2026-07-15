"""Service to import legacy db.json articles into the database."""
import json
import os
import re
import unicodedata
import ipaddress
from urllib.parse import urlparse
from flask import current_app
from app.extensions import db
from app.models.article import (
    Article,
    ArticleKeyFact,
    ArticleTimelineEvent,
    ArticleRelatedPlace,
    ArticleSource,
    ArticleStatus,
)
from app.models.category import Category
from app.models.tag import Tag
from app.services.taxonomy_service import slugify
from app.utils.logging_helper import log_activity


ALLOWED_SOURCE_KINDS = {"oficial", "institucional", "biblioteca", "mapa", "referencia", "imagen"}


def _is_safe_url(url: str) -> bool:
    """Validate URL schema and reject localhost/private IPs to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.hostname:
            return False
        if parsed.hostname in ("localhost", "0.0.0.0", "::1", "127.0.0.1"):
            return False
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            pass
        return True
    except Exception:
        return False


class WikiImportService:
    @staticmethod
    def import_json(filepath: str, user=None, dry_run: bool = False,
                    update_existing: bool = False, download_images: bool = False,
                    publish: bool = False, continue_on_error: bool = False) -> dict:
        report = {
            "read": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "imported_images": 0,
            "error_details": [],
        }

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        articles = data.get("articles", [])
        report["read"] = len(articles)

        for art_data in articles:
            try:
                result = WikiImportService._import_one(
                    art_data, user=user, dry_run=dry_run,
                    update_existing=update_existing,
                    download_images=download_images,
                    publish=publish,
                )
                if result == "created":
                    report["created"] += 1
                elif result == "updated":
                    report["updated"] += 1
                elif result == "skipped":
                    report["skipped"] += 1
                elif result == "image":
                    report["imported_images"] += 1
            except Exception as e:
                report["errors"] += 1
                report["error_details"].append(f"{art_data.get('slug', '?')}: {str(e)}")
                if not continue_on_error:
                    break

        return report

    @staticmethod
    def _import_one(art_data, user=None, dry_run=False, update_existing=False,
                    download_images=False, publish=False) -> str:
        slug = art_data.get("slug")
        if not slug:
            raise ValueError("Artículo sin slug")

        existing = Article.query.filter_by(slug=slug).first()
        if existing and not update_existing:
            return "skipped"

        category_name = art_data.get("category")
        category = None
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(
                    name=category_name,
                    slug=slugify(category_name),
                    is_active=True,
                    sort_order=0,
                )
                db.session.add(category)
                db.session.flush()

        tags = []
        for tag_name in art_data.get("tags", []):
            tag_slug = slugify(tag_name)
            tag = Tag.query.filter_by(slug=tag_slug).first()
            if not tag:
                tag = Tag(name=tag_name, slug=tag_slug)
                db.session.add(tag)
                db.session.flush()
            tags.append(tag)

        coords = art_data.get("coordinates", {})
        street_ev = art_data.get("streetEvidence", {})

        status = ArticleStatus.DRAFT.value
        if publish:
            has_title = bool(art_data.get("title"))
            has_summary = bool(art_data.get("summary"))
            has_body = bool(art_data.get("body"))
            has_category = bool(category)
            has_sources = bool(art_data.get("sources", []))
            if all([has_title, has_summary, has_body, has_category, has_sources]):
                status = ArticleStatus.PUBLISHED.value
            else:
                status = ArticleStatus.DRAFT.value

        if existing and update_existing:
            existing.title = art_data.get("title", existing.title)
            existing.subtitle = art_data.get("subtitle", existing.subtitle)
            existing.type = art_data.get("type", existing.type)
            existing.street_name = art_data.get("streetName", existing.street_name)
            existing.period = art_data.get("period", existing.period)
            existing.birth_place = art_data.get("birthPlace", existing.birth_place)
            existing.death_place = art_data.get("deathPlace", existing.death_place)
            existing.category_id = category.id if category else existing.category_id
            existing.summary = art_data.get("summary", existing.summary)
            existing.image_alt = art_data.get("imageAlt", existing.image_alt)
            existing.image_credit = art_data.get("imageCredit", existing.image_credit)
            existing.latitude = coords.get("lat") if isinstance(coords, dict) else None
            existing.longitude = coords.get("lng") if isinstance(coords, dict) else None
            existing.coordinate_confidence = coords.get("confidence") if isinstance(coords, dict) else None
            existing.coordinate_note = coords.get("note") if isinstance(coords, dict) else None
            existing.street_evidence_status = street_ev.get("status") if isinstance(street_ev, dict) else None
            existing.street_evidence_note = street_ev.get("note") if isinstance(street_ev, dict) else None
            existing.historical_context = art_data.get("historicalContext", existing.historical_context)
            existing.source_notes = art_data.get("sourceNotes", existing.source_notes)
            existing.body_markdown = art_data.get("body", existing.body_markdown)

            if status == "published" and existing.status != "published":
                from datetime import datetime
                existing.status = "published"
                existing.published_at = datetime.utcnow()
                existing.published_by_id = user.id if user else None

            existing.tags = tags
            existing.version += 1

            ArticleKeyFact.query.filter_by(article_id=existing.id).delete()
            ArticleTimelineEvent.query.filter_by(article_id=existing.id).delete()
            ArticleRelatedPlace.query.filter_by(article_id=existing.id).delete()
            ArticleSource.query.filter_by(article_id=existing.id).delete()

            WikiImportService._create_children(existing, art_data)

            if not dry_run:
                db.session.commit()
            return "updated"

        article = Article(
            slug=slug,
            title=art_data.get("title", slug),
            subtitle=art_data.get("subtitle"),
            type=art_data.get("type"),
            street_name=art_data.get("streetName"),
            period=art_data.get("period"),
            birth_place=art_data.get("birthPlace"),
            death_place=art_data.get("deathPlace"),
            category_id=category.id if category else None,
            summary=art_data.get("summary"),
            image_alt=art_data.get("imageAlt"),
            image_credit=art_data.get("imageCredit"),
            latitude=coords.get("lat") if isinstance(coords, dict) else None,
            longitude=coords.get("lng") if isinstance(coords, dict) else None,
            coordinate_confidence=coords.get("confidence") if isinstance(coords, dict) else None,
            coordinate_note=coords.get("note") if isinstance(coords, dict) else None,
            street_evidence_status=street_ev.get("status") if isinstance(street_ev, dict) else None,
            street_evidence_note=street_ev.get("note") if isinstance(street_ev, dict) else None,
            historical_context=art_data.get("historicalContext"),
            source_notes=art_data.get("sourceNotes"),
            body_markdown=art_data.get("body"),
            status=status,
            featured=False,
            created_by_id=user.id if user else None,
            updated_by_id=user.id if user else None,
            version=1,
        )
        if status == "published":
            from datetime import datetime
            article.published_at = datetime.utcnow()
            article.published_by_id = user.id if user else None

        db.session.add(article)
        db.session.flush()
        article.tags = tags

        WikiImportService._create_children(article, art_data)

        if not dry_run:
            db.session.commit()

        return "created"

    @staticmethod
    def _create_children(article, art_data):
        for i, fact in enumerate(art_data.get("keyFacts", [])):
            db.session.add(ArticleKeyFact(article_id=article.id, text=fact, position=i))

        for i, event in enumerate(art_data.get("timeline", [])):
            db.session.add(ArticleTimelineEvent(
                article_id=article.id,
                year=event.get("year", ""),
                event=event.get("event", ""),
                position=i,
            ))

        for i, place in enumerate(art_data.get("relatedPlaces", [])):
            db.session.add(ArticleRelatedPlace(
                article_id=article.id,
                name=place.get("name", ""),
                description=place.get("description", ""),
                type=place.get("type", ""),
                position=i,
            ))

        for i, source in enumerate(art_data.get("sources", [])):
            url = source.get("url", "")
            kind = source.get("kind", "referencia")
            if kind not in ALLOWED_SOURCE_KINDS:
                kind = "referencia"
            if url and _is_safe_url(url):
                db.session.add(ArticleSource(
                    article_id=article.id,
                    label=source.get("label", ""),
                    url=url,
                    kind=kind,
                    position=i,
                ))