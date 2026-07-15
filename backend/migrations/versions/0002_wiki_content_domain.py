"""Wiki content domain

Revision ID: 0002_wiki_content_domain
Revises: 0001_initial
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_wiki_content_domain'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('slug', sa.String(120), unique=True, nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)

    # Tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(80), unique=True, nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_tags_slug', 'tags', ['slug'], unique=True)

    # Media assets
    op.create_table(
        'media_assets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', sa.String(36), unique=True, nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('object_name', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('extension', sa.String(10), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('checksum_sha256', sa.String(64), nullable=True),
        sa.Column('small_object', sa.String(500), nullable=True),
        sa.Column('medium_object', sa.String(500), nullable=True),
        sa.Column('large_object', sa.String(500), nullable=True),
        sa.Column('original_object', sa.String(500), nullable=True),
        sa.Column('small_width', sa.Integer(), nullable=True),
        sa.Column('small_height', sa.Integer(), nullable=True),
        sa.Column('medium_width', sa.Integer(), nullable=True),
        sa.Column('medium_height', sa.Integer(), nullable=True),
        sa.Column('large_width', sa.Integer(), nullable=True),
        sa.Column('large_height', sa.Integer(), nullable=True),
        sa.Column('alt_text', sa.String(500), nullable=True),
        sa.Column('caption', sa.String(500), nullable=True),
        sa.Column('credit', sa.String(255), nullable=True),
        sa.Column('license', sa.String(100), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('uploaded_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_media_assets_uuid', 'media_assets', ['uuid'], unique=True)
    op.create_index('ix_media_assets_checksum', 'media_assets', ['checksum_sha256'])

    # Article tags association
    op.create_table(
        'article_tags',
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id'), primary_key=True),
    )

    # Articles
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(200), unique=True, nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('subtitle', sa.String(500), nullable=True),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('street_name', sa.String(200), nullable=True),
        sa.Column('period', sa.String(100), nullable=True),
        sa.Column('birth_place', sa.String(200), nullable=True),
        sa.Column('death_place', sa.String(200), nullable=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('hero_media_id', sa.Integer(), sa.ForeignKey('media_assets.id'), nullable=True),
        sa.Column('image_alt', sa.String(500), nullable=True),
        sa.Column('image_credit', sa.String(500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('coordinate_confidence', sa.String(20), nullable=True),
        sa.Column('coordinate_note', sa.Text(), nullable=True),
        sa.Column('street_evidence_status', sa.String(20), nullable=True),
        sa.Column('street_evidence_note', sa.Text(), nullable=True),
        sa.Column('historical_context', sa.Text(), nullable=True),
        sa.Column('source_notes', sa.Text(), nullable=True),
        sa.Column('body_markdown', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('seo_title', sa.String(200), nullable=True),
        sa.Column('seo_description', sa.String(300), nullable=True),
        sa.Column('canonical_url', sa.String(500), nullable=True),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('published_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )
    op.create_index('ix_articles_slug', 'articles', ['slug'], unique=True)
    op.create_index('ix_articles_status', 'articles', ['status'])
    op.create_index('ix_articles_published_at', 'articles', ['published_at'])
    op.create_index('ix_articles_updated_at', 'articles', ['updated_at'])
    op.create_index('ix_articles_category_id', 'articles', ['category_id'])
    op.create_index('ix_articles_featured', 'articles', ['featured'])
    op.create_index('ix_articles_deleted_at', 'articles', ['deleted_at'])
    op.create_index('ix_articles_status_published', 'articles', ['status', 'published_at'])

    # Article key facts
    op.create_table(
        'article_key_facts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_article_key_facts_article_id', 'article_key_facts', ['article_id'])

    # Article timeline events
    op.create_table(
        'article_timeline_events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('year', sa.String(50), nullable=False),
        sa.Column('event', sa.Text(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_article_timeline_article_id', 'article_timeline_events', ['article_id'])

    # Article related places
    op.create_table(
        'article_related_places',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(100), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_article_related_places_article_id', 'article_related_places', ['article_id'])

    # Article sources
    op.create_table(
        'article_sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('label', sa.String(300), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('kind', sa.String(20), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accessed_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_article_sources_article_id', 'article_sources', ['article_id'])

    # Article revisions
    op.create_table(
        'article_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id'), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_json', sa.Text(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.String(200), nullable=True),
    )
    op.create_index('ix_article_revisions_article_id', 'article_revisions', ['article_id'])


def downgrade():
    op.drop_table('article_revisions')
    op.drop_table('article_sources')
    op.drop_table('article_related_places')
    op.drop_table('article_timeline_events')
    op.drop_table('article_key_facts')
    op.drop_index('ix_articles_status_published', 'articles')
    op.drop_index('ix_articles_deleted_at', 'articles')
    op.drop_index('ix_articles_featured', 'articles')
    op.drop_index('ix_articles_category_id', 'articles')
    op.drop_index('ix_articles_updated_at', 'articles')
    op.drop_index('ix_articles_published_at', 'articles')
    op.drop_index('ix_articles_status', 'articles')
    op.drop_index('ix_articles_slug', 'articles')
    op.drop_table('articles')
    op.drop_table('article_tags')
    op.drop_index('ix_media_assets_checksum', 'media_assets')
    op.drop_index('ix_media_assets_uuid', 'media_assets')
    op.drop_table('media_assets')
    op.drop_index('ix_tags_slug', 'tags')
    op.drop_table('tags')
    op.drop_index('ix_categories_slug', 'categories')
    op.drop_table('categories')