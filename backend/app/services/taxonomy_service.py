"""Category and Tag management services."""
import re
import unicodedata
from app.extensions import db
from app.models.category import Category
from app.models.tag import Tag
from app.models.article import Article
from app.utils.logging_helper import log_activity


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


class CategoryService:
    @staticmethod
    def list_all():
        return Category.query.order_by(Category.sort_order, Category.name).all()

    @staticmethod
    def list_active():
        return Category.query.filter_by(is_active=True).order_by(Category.sort_order, Category.name).all()

    @staticmethod
    def get(slug_or_id):
        if isinstance(slug_or_id, int) or (isinstance(slug_or_id, str) and slug_or_id.isdigit()):
            return Category.query.get(int(slug_or_id))
        return Category.query.filter_by(slug=slug_or_id).first()

    @staticmethod
    def create(name, description=None, sort_order=0, is_active=True, user=None):
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        cat = Category(name=name, slug=slug, description=description, sort_order=sort_order, is_active=is_active)
        db.session.add(cat)
        db.session.commit()
        log_activity(action="CATEGORY_CREATE", details=f"Categoría creada: {cat.name}", user=user)
        return cat

    @staticmethod
    def update(cat: Category, data: dict, user=None):
        if "name" in data:
            cat.name = data["name"]
        if "description" in data:
            cat.description = data["description"]
        if "sortOrder" in data:
            cat.sort_order = data["sortOrder"]
        if "isActive" in data:
            cat.is_active = data["isActive"]
        db.session.commit()
        log_activity(action="CATEGORY_UPDATE", details=f"Categoría actualizada: {cat.name}", user=user)
        return cat

    @staticmethod
    def delete(cat: Category, user=None):
        count = Article.query.filter_by(category_id=cat.id, deleted_at=None).count()
        if count > 0:
            raise ValueError("No se puede eliminar una categoría con artículos asociados.")
        name = cat.name
        db.session.delete(cat)
        db.session.commit()
        log_activity(action="CATEGORY_DELETE", details=f"Categoría eliminada: {name}", user=user)


class TagService:
    @staticmethod
    def list_all():
        return Tag.query.order_by(Tag.name).all()

    @staticmethod
    def get_or_create(name: str) -> Tag:
        slug = slugify(name)
        tag = Tag.query.filter_by(slug=slug).first()
        if not tag:
            tag = Tag(name=name, slug=slug)
            db.session.add(tag)
            db.session.flush()
        return tag

    @staticmethod
    def create(name, user=None):
        tag = TagService.get_or_create(name)
        db.session.commit()
        log_activity(action="TAG_CREATE", details=f"Etiqueta creada: {tag.name}", user=user)
        return tag

    @staticmethod
    def delete(tag: Tag, user=None):
        name = tag.name
        db.session.delete(tag)
        db.session.commit()
        log_activity(action="TAG_DELETE", details=f"Etiqueta eliminada: {name}", user=user)