# WikiLavalleja Backend

Flask 3.1 backend that powers WikiLavalleja. It serves both a public JSON API
and a server-rendered admin panel for editorial work. It uses MariaDB/MySQL
for data, Redis for rate limiting, and MinIO for image storage.

---

## What this backend includes

- **Flask** application factory (`create_app`) with environment-based config
  (`development` / `production` / `testing`).
- **Session-based authentication** with Flask-Login, Argon2 password hashing,
  and a math captcha on the login form.
- **Two-factor authentication (2FA)** — 6-digit code emailed to the admin
  user, stored Argon2-hashed in the database, with 10-minute expiry and
  single-use enforcement. `attempts` counter and `MAX_2FA_ATTEMPTS` lockout.
- **Wiki content domain** — full CRUD for articles, categories, tags, sources,
  timeline events, key facts, related places, and revisions, with optimistic
  concurrency control via `version`.
- **Public JSON API** under `/api/v1/` with pagination, search, filters, and
  ordering. Articles serialize to camelCase.
- **Admin JSON API** under `/api/v1/admin/` for the editorial panel.
- **Server-rendered admin panel** (Jinja2 + Tailwind) with article listing,
  article editor, media library, revisions, and user management.
- **Media pipeline** — upload to MinIO, process with Pillow (WebP, EXIF
  orientation, SHA-256, multiple variants), and serve via the API.
- **Redis** integration for rate-limiting storage (with automatic fallback
  to in-memory if Redis is unavailable).
- **MinIO** object storage with bucket auto-creation and variants (small,
  medium, large, original).
- **PostgreSQL/MySQL/MariaDB** via SQLAlchemy + Flask-Migrate (Alembic) with
  two migrations: initial auth/audit and the wiki content domain.
- **Prometheus** metrics endpoint (`/metrics`) with multiprocess support.
- **Healthcheck** endpoints (`/health/live`, `/health/ready`) used by
  Docker/Coolify.
- **Security**: Flask-Talisman (CSP + HSTS in production), CSRF protection,
  secure cookie flags, rate limiting, Argon2 hashing, session regeneration
  on 2FA, POST logout with CSRF.
- **Audit logging** (`ActivityLog`) — silently records auth, user
  management, and editorial actions.

---

## Domain model

```
categories                   (id, name, slug, description, sort_order, is_active)
tags                         (id, name, slug)
articles                     (id, slug, title, subtitle, type, street_name, period,
                              birth_place, death_place, category_id, summary,
                              hero_media_id, image_alt, image_credit, latitude,
                              longitude, coordinate_confidence, coordinate_note,
                              street_evidence_status, street_evidence_note,
                              historical_context, source_notes, body_markdown,
                              status, featured, seo_*, canonical_url,
                              created_by_id, updated_by_id, published_by_id,
                              created_at, updated_at, published_at, archived_at,
                              deleted_at, version)
article_tags                 (article_id, tag_id)  — many-to-many
article_key_facts            (id, article_id, text, position)
article_timeline_events      (id, article_id, year, event, position)
article_related_places       (id, article_id, name, description, type, position)
article_sources              (id, article_id, label, url, kind, position,
                              accessed_at)
article_revisions            (id, article_id, revision_number, snapshot_json,
                              created_by_id, created_at, reason)
media_assets                 (id, uuid, original_filename, object_name, mime_type,
                              extension, size_bytes, width, height,
                              checksum_sha256, [small/medium/large/original]_object,
                              [small/medium/large]_width/height, alt_text, caption,
                              credit, license, source_url, is_public,
                              uploaded_by_id, created_at, updated_at, deleted_at)
users                        (id, username, email, password_hash, is_active,
                              is_superuser, created_at, last_login_at)
two_factor_codes             (id, user_id, code_hash, expires_at, attempts,
                              consumed_at, created_at)
activity_logs                (id, user_id, username, action, details, ip_address,
                              user_agent, created_at)
```

---

## API endpoints

### Public API (no auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/articles` | List with `q`, `category`, `type`, `tag`, `featured`, `page`, `perPage`, `sort` |
| GET | `/api/v1/articles/<slug>` | Article detail |
| GET | `/api/v1/categories` | Active categories |
| GET | `/api/v1/tags` | Tags used in published articles |
| GET | `/api/v1/media/<uuid>/content/<variant>` | Media content (small/medium/large/original) |
| GET | `/api/v1/sitemap` | Dynamic XML sitemap |

### Admin API (session + 2FA + CSRF required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/admin/articles` | List/create |
| GET/PATCH/DELETE | `/api/v1/admin/articles/<id>` | Read/update/delete |
| POST | `/api/v1/admin/articles/<id>/publish` | Publish |
| POST | `/api/v1/admin/articles/<id>/unpublish` | Unpublish |
| POST | `/api/v1/admin/articles/<id>/archive` | Archive |
| POST | `/api/v1/admin/articles/<id>/restore` | Restore |
| POST | `/api/v1/admin/articles/<id>/duplicate` | Duplicate as draft |
| GET | `/api/v1/admin/articles/<id>/revisions` | Revision list |
| POST | `/api/v1/admin/articles/<id>/revisions/<rev_id>/restore` | Restore revision |
| POST | `/api/v1/admin/articles/<id>/autosave` | Lightweight autosave |
| GET/POST | `/api/v1/admin/categories` | Categories CRUD |
| GET/POST | `/api/v1/admin/tags` | Tags CRUD |
| GET/POST | `/api/v1/admin/media` | List/upload |
| GET/PATCH/DELETE | `/api/v1/admin/media/<uuid>` | Manage/delete |
| GET | `/api/v1/admin/media/<uuid>/usage` | Check usage |

### Admin panel (Jinja2)

| Path | Description |
|------|-------------|
| `/admin/login` | Login form with math captcha |
| `/admin/2fa` | 2FA verification |
| `/admin/dashboard` | Metrics and recent activity |
| `/admin/articles` | Article list with filters |
| `/admin/articles/new` | New article editor |
| `/admin/articles/<id>/edit` | Article editor |
| `/admin/articles/<id>/revisions` | Revision history |
| `/admin/media` | Media library |
| `/admin/users` | User management (super admin) |
| `/admin/logs` | Activity log (super admin) |
| `/admin/logs/export` | CSV export of activity log |

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values. See `.env.example`
for the full list and comments. The key variables are:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Flask session signing key (required, long & random) |
| `WTF_CSRF_SECRET_KEY` | CSRF token key (defaults to SECRET_KEY if unset) |
| `DATABASE_URL` | SQLAlchemy database URI (MariaDB, MySQL, or PostgreSQL) |
| `REDIS_URL` | Redis connection URL (or REDIS_HOST/PORT/DB/PASSWORD) |
| `MINIO_ENDPOINT` / `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | MinIO credentials |
| `MINIO_BUCKET_NAME` | MinIO bucket (auto-created on startup) |
| `MAIL_SERVER` / `MAIL_USERNAME` / `MAIL_PASSWORD` | SMTP for 2FA emails |
| `CORS_ORIGINS` | Comma-separated allowed origins for API CORS |
| `FLASK_CONFIG` | `development` / `production` / `testing` |
| `APP_BASE_URL` | Public URL of the backend (used for sitemap, canonical URLs) |
| `FRONTEND_URL` | Public URL of the frontend (fallback CORS) |
| `WIKI_MEDIA_MAX_BYTES` | Max upload size (default 10 MB) |
| `WIKI_MEDIA_SMALL_WIDTH` / `MEDIUM_WIDTH` / `LARGE_WIDTH` | Image variant widths |
| `ENABLE_2FA_CODE_LOGGING` | Set to True to log codes to stdout (dev only) |
| `MAX_2FA_ATTEMPTS` | Max 2FA attempts before invalidation (default 5) |
| `SESSION_LIFETIME_MINUTES` | Session lifetime (default 480) |
| `OPENAPI_ENABLED` | Toggle OpenAPI docs |

Gunicorn tuning variables (`GUNICORN_WORKERS`, `PORT`, etc.) and Prometheus
(`PROMETHEUS_MULTIPROC_DIR`) are also supported — see `.env.example`.

---

## How to run locally

### 1. Create a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env     # Linux/Mac
copy .env.example .env   # Windows
```

Edit `.env` with your database, Redis, MinIO, and mail credentials. Set
`FLASK_ENV=development`, `FLASK_CONFIG=development`, `FLASK_DEBUG=1`.

### 4. Initialize the database

```bash
flask db upgrade
```

This applies both migrations: `0001_initial.py` (users, 2FA, audit) and
`0002_wiki_content_domain.py` (articles, categories, tags, media, etc.).

### 5. Create the first admin user

```bash
flask create-admin admin admin@example.com MyStrongPass123 true
```

The last argument (`true`) makes this a superuser.

### 6. (Optional) Initialize MinIO bucket and import legacy data

```bash
flask init-bucket
flask import-wiki-data ../data/db.json --publish
```

`import-wiki-data` reads the legacy `data/db.json`, creates categories and
tags as needed, and creates article records with their children (key facts,
timeline, places, sources). `--publish` will publish valid articles
immediately; omit it to leave them as drafts.

### 7. Run the app

```bash
flask run
# or
python wsgi.py
```

The app will be available at `http://127.0.0.1:5000`:
- `/admin/login` — editorial panel
- `/api/v1/articles` — public JSON API
- `/health/live` — liveness probe
- `/health/ready` — readiness probe

---

## CLI commands

```bash
flask create-admin <username> <email> <password> [true|false]  # Create admin user
flask rotate-secret                                            # Generate a SECRET_KEY
flask init-bucket                                              # Verify/create MinIO bucket
flask import-wiki-data <path> [--dry-run] [--update-existing]   # Import articles from JSON
                       [--publish] [--continue-on-error]
flask db upgrade                                               # Apply migrations
flask db migrate -m "Description"                              # Generate a migration
flask routes                                                   # List all routes
```

---

## How auth works

- **Login flow**: `GET /admin/login` shows a login form with a math captcha.
  `POST` validates the captcha, looks up the user by email, verifies the
  Argon2 password hash, then generates a 6-digit 2FA code, stores its Argon2
  hash in the `two_factor_codes` table, and emails it. The user is redirected
  to `/admin/2fa`.
- **2FA flow**: `POST /admin/2fa` looks up the most recent unconsumed code
  for the user, verifies it (Argon2), marks it consumed, and calls
  `login_user()`. The session is cleared and regenerated after 2FA
  completion. Codes expire after 10 minutes, can only be used once, and the
  `attempts` counter is incremented on every failed try. After
  `MAX_2FA_ATTEMPTS` failed attempts, the code is invalidated.
- **Sessions**: Flask-Login session cookies with `HttpOnly`, `SameSite=Lax`,
  and `Secure` (in production).
- **Rate limiting**: login is limited to 5/min, 2FA to 10/min (via
  Flask-Limiter, backed by Redis when available).
- **Logout**: `POST /admin/logout` with CSRF, clears the session.
- **Roles**: `User.is_superuser` gates access to user management, publishing,
  archiving, and full audit access. Regular admins can edit articles and
  upload media.

---

## How 2FA works (security-focused)

- Codes are 6-digit, generated with `secrets.choice` (cryptographically
  secure).
- Codes are **hashed with Argon2** before storage — the plaintext code is
  never written to the database.
- Codes expire after 10 minutes (`expires_at`).
- Codes are single-use (`consumed_at` is set on successful verification).
- Codes are emailed asynchronously via Flask-Mail (synchronously in debug
  mode).
- The `attempts` field is incremented on every failed verification. After
  `MAX_2FA_ATTEMPTS`, the code is marked as consumed (invalidated).
- Previous unused codes are invalidated when a new code is generated.
- The plaintext code is **never** logged to stdout. Set
  `ENABLE_2FA_CODE_LOGGING=True` in development to log codes for testing.
- Failed attempts are logged to `ActivityLog` with action `LOGIN` and a
  generic message (no enumeration clues).

---

## How Redis is used

- Redis is probed at app startup (`init_redis` in `redis_utils.py`). If
  unavailable, `REDIS_AVAILABLE` is set to `False` and the app continues.
- **Flask-Limiter** uses Redis as its storage backend when available
  (`RATELIMIT_STORAGE_URL = REDIS_URL`). If Redis is down, it falls back to
  `memory://` so the app keeps working (rate limits won't persist across
  workers).
- Redis URL is built from `REDIS_URL` (full URL) or from individual
  `REDIS_HOST`/`REDIS_PORT`/`REDIS_DB`/`REDIS_PASSWORD` env vars.

---

## How MinIO is used

- `MinioService` (`app/services/minio_service.py`) initializes the MinIO
  client at app startup (non-fatal if unavailable).
- `ensure_bucket_exists()` creates the bucket if missing.
- `MediaService` processes uploaded images with Pillow:
  - Detects real MIME type (not file extension)
  - Corrects EXIF orientation
  - Converts to WebP with configurable quality
  - Generates variants: small (480px), medium (960px), large (1600px)
  - Computes SHA-256 checksum
  - Stores UUIDs as object names (no original filenames exposed)
- `get_file_content()` serves media through the API
  (`/api/v1/media/<uuid>/content/<variant>`), avoiding public bucket
  exposure.

---

## How to deploy on Coolify

This backend is pre-configured for Coolify:

1. **Create a new service** in Coolify pointing to this repository.
2. **Set the Dockerfile path** to `./Dockerfile` (Coolify auto-detects it).
3. **Add environment variables** in the Coolify service settings (same as
   `.env.example` but with production values). At minimum:
   - `FLASK_CONFIG=production`
   - `SECRET_KEY` and `WTF_CSRF_SECRET_KEY` (long random strings)
   - `DATABASE_URL` (point to your Coolify-managed database)
   - `REDIS_URL` (point to your Coolify-managed Redis)
   - `MINIO_*` (point to your Coolify-managed MinIO)
   - `MAIL_*` (your SMTP provider)
   - `CORS_ORIGINS` (your frontend URL)
   - `APP_BASE_URL` (your backend public URL)
4. **Expose port 5000** (the Dockerfile default).
5. **Healthcheck** is built into the Dockerfile (`GET /health`).
6. **Deploy**. The `entrypoint.sh` will automatically run
   `flask db upgrade` and then start Gunicorn. If the migration fails, the
   container will **not** start, surfacing the error.

After deployment:

```bash
# Create the first admin
flask create-admin admin admin@example.com MyStrongPass123 true

# Initialize MinIO bucket
flask init-bucket

# Import legacy articles
flask import-wiki-data /path/to/data/db.json --publish
```

### Gunicorn / Docker

- `entrypoint.sh` runs migrations then `gunicorn -c gunicorn.conf.py "wsgi:app"`.
- `gunicorn.conf.py` reads `PORT`, `GUNICORN_WORKERS`, `GUNICORN_THREADS`,
  etc. from environment.
- Prometheus multiprocess dir is set up automatically.
- `ProxyFix` is configured for 1 hop (Coolify).

---

## Project structure

```
backend/
├── app/
│   ├── __init__.py          # create_app factory
│   ├── commands.py           # CLI commands
│   ├── config.py             # Config classes (dev/prod/testing)
│   ├── error_handlers.py     # JSON/HTML error handlers
│   ├── extensions.py         # Flask extensions (unbound)
│   ├── health.py             # /health/live, /health/ready
│   ├── metrics.py            # Prometheus metrics
│   ├── redis_utils.py        # Redis URL builder + probe
│   ├── forms/                # WTForms (admin + auth)
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py           # User, TwoFactorCode
│   │   ├── audit.py          # ActivityLog
│   │   ├── article.py        # Article + children + ArticleStatus
│   │   ├── category.py       # Category
│   │   ├── tag.py            # Tag
│   │   └── media_asset.py    # MediaAsset
│   ├── schemas/              # Marshmallow schemas
│   │   └── wiki_schemas.py   # Article, Category, Tag, Media, etc.
│   ├── services/             # Business logic
│   │   ├── article_service.py
│   │   ├── article_query_service.py
│   │   ├── publication_service.py
│   │   ├── revision_service.py
│   │   ├── media_service.py
│   │   ├── media_resolver.py
│   │   ├── taxonomy_service.py
│   │   ├── wiki_import_service.py
│   │   ├── minio_service.py
│   │   └── mail_service.py
│   ├── routes/
│   │   ├── admin/            # Server-rendered admin panel
│   │   └── api/              # JSON API
│   │       ├── public_routes.py
│   │       └── admin_routes.py
│   ├── templates/            # Jinja2 templates
│   │   ├── admin/
│   │   ├── emails/
│   │   └── errors.html
│   └── utils/                # security, logging helpers
├── migrations/               # Alembic migrations
│   └── versions/
│       ├── 0001_initial.py
│       └── 0002_wiki_content_domain.py
├── public/                   # Static assets (CSS, JS, favicon)
├── .env.example
├── Dockerfile
├── docker-compose.dev.yml    # Dev services
├── entrypoint.sh
├── gunicorn.conf.py
├── manage.py
├── requirements.txt
└── wsgi.py
```

---

## License

WikiLavalleja backend — use freely for the WikiLavalleja project.
