# WikiLavalleja

A civic Wikipedia-style platform dedicated to preserving the historical, cultural and biographical memory of the department of Lavalleja, Uruguay. WikiLavalleja is built as two integrated projects sharing a single repository:

- A **public frontend** (React 19 + Vite + TypeScript + Tailwind 4 + DaisyUI) that renders articles for visitors.
- A **backend** (Flask 3 + SQLAlchemy 2 + MariaDB + Redis + MinIO) that exposes a public API and a server-rendered admin panel for editorial work.

## Repository layout

```
.
├── backend/              Flask backend + admin panel + migrations
│   ├── app/
│   │   ├── models/        SQLAlchemy models (User, Article, Category, Tag, Media, ...)
│   │   ├── schemas/       Marshmallow schemas (camelCase)
│   │   ├── services/      Business logic (articles, media, import, etc.)
│   │   ├── routes/
│   │   │   ├── admin/     Server-rendered admin panel
│   │   │   └── api/       JSON API (public + admin)
│   │   ├── templates/     Jinja2 templates
│   │   └── commands.py    CLI commands (create-admin, import-wiki-data, ...)
│   ├── migrations/        Alembic migrations
│   ├── Dockerfile
│   ├── docker-compose.dev.yml
│   ├── entrypoint.sh
│   ├── gunicorn.conf.py
│   ├── requirements.txt
│   └── .env.example
├── src/                   React frontend
│   ├── components/        UI components
│   ├── pages/              Route pages
│   ├── lib/api.ts          Backend API client
│   ├── types/              TypeScript types
│   ├── stores/             Zustand stores
│   └── styles/             Global CSS
├── data/db.json            Legacy article dataset (used for migration)
├── public/                 Static frontend assets
├── docker-compose.dev.yml   Dev services (MariaDB, Redis, MinIO, Mailpit)
├── Dockerfile              Frontend container
├── nginx.conf              Frontend nginx config
├── .env.example            Frontend env vars
├── infraesructura.md       Architecture document
└── IMPLEMENTATION_REPORT.md  Detailed implementation report
```

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite 8, TypeScript 6, TailwindCSS 4, DaisyUI 5, TanStack Query 5, react-markdown 10, react-helmet-async |
| Theme | Zustand store, CSS variables under `html.dark`, persists in localStorage |
| Backend | Flask 3.1, SQLAlchemy 2, Flask-Migrate, Marshmallow 4, Flask-Login, Flask-WTF (CSRF), Flask-Talisman, Flask-Mail, Flask-Limiter, Flask-CORS |
| Storage | MariaDB/MySQL (data), Redis (rate limit, cache), MinIO (media) |
| Auth | Session-based + email 2FA (Argon2 hashed codes, 10 min expiry) |
| Editor | Server-rendered Jinja2 + vanilla JS (admin), full Markdown editor with repeaters for facts, timeline, places, sources |
| Server | Gunicorn (4 workers × 4 threads, /dev/shm) |
| Observability | Prometheus multiprocess metrics, /health/live, /health/ready |
| Deploy | Docker (backend), Docker (frontend with nginx), Coolify-ready |

## Quick start (local development)

### 1. Start infrastructure services

```bash
docker compose -f docker-compose.dev.yml up -d
```

This starts MariaDB, Redis, MinIO and Mailpit.

### 2. Configure environment

```bash
# Frontend
cp .env.example .env

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env: SECRET_KEY, DATABASE_URL, MAIL_*, MINIO_*
```

### 3. Backend setup

```bash
cd backend
python -m pip install -r requirements.txt
python -m flask db upgrade
python -m flask create-admin admin admin@example.com MyStrongPass123 true
python -m flask init-bucket
python -m flask import-wiki-data ../data/db.json --publish
python wsgi.py
```

The backend runs on http://localhost:5000:
- `/admin/login` — editorial panel
- `/admin/articles` — article management
- `/api/v1/articles` — public JSON API
- `/health/live` — liveness probe
- `/health/ready` — readiness probe

### 4. Frontend setup

```bash
npm install
npm run dev
```

The frontend runs on http://localhost:5173 and consumes the Flask API.

## API

Public endpoints (no auth):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/articles` | Paginated article list with search, filters, sorting |
| GET | `/api/v1/articles/<slug>` | Article detail with all relations |
| GET | `/api/v1/categories` | Active categories with article counts |
| GET | `/api/v1/tags` | Tags used in published articles |
| GET | `/api/v1/media/<uuid>/content/<variant>` | Media content (small, medium, large, original) |
| GET | `/api/v1/sitemap` | Dynamic XML sitemap |

Admin endpoints (session + 2FA + CSRF required):

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/v1/admin/articles` | List/create articles |
| GET/PATCH/DELETE | `/api/v1/admin/articles/<id>` | Read/update/delete |
| POST | `/api/v1/admin/articles/<id>/publish` | Publish |
| POST | `/api/v1/admin/articles/<id>/unpublish` | Unpublish |
| POST | `/api/v1/admin/articles/<id>/archive` | Archive |
| POST | `/api/v1/admin/articles/<id>/restore` | Restore (un-archive) |
| POST | `/api/v1/admin/articles/<id>/duplicate` | Duplicate as draft |
| GET | `/api/v1/admin/articles/<id>/revisions` | Revision history |
| POST | `/api/v1/admin/articles/<id>/revisions/<rev_id>/restore` | Restore revision |
| POST | `/api/v1/admin/articles/<id>/autosave` | Lightweight autosave |
| GET/POST | `/api/v1/admin/categories` | Categories CRUD |
| GET/POST | `/api/v1/admin/tags` | Tags CRUD |
| GET/POST | `/api/v1/admin/media` | List/upload media |
| GET/PATCH/DELETE | `/api/v1/admin/media/<uuid>` | Manage metadata / delete |
| GET | `/api/v1/admin/media/<uuid>/usage` | Check where media is referenced |

## Domain model

```
categories
tags
articles ──┬─ article_tags ──── tags
           ├─ article_key_facts
           ├─ article_timeline_events
           ├─ article_related_places
           ├─ article_sources
           └─ article_revisions
media_assets
users ──── two_factor_codes
       └── activity_logs
```

Articles have status: `draft` → `review` → `published` → `archived`. Only `published` articles appear in the public API. `deleted_at` enables soft deletion.

## Roles and permissions

| Role | Can do |
|------|--------|
| Inactive user | Nothing (login blocked) |
| Admin (active, not superuser) | Login, dashboard, create/edit articles, upload media, view revisions |
| Super admin | Everything + user management, publish/unpublish/archive, force-delete, full audit access |

## Security

- **2FA**: 6-digit code by email, Argon2-hashed in DB, 10 min expiry, single-use, max 5 attempts then invalidated. Previous unused codes are invalidated when a new one is created. Code is never logged to stdout unless `ENABLE_2FA_CODE_LOGGING=True`.
- **Sessions**: `HttpOnly`, `SameSite=Lax`, `Secure` in production, regenerated on 2FA completion (anti-fixation).
- **CSRF**: Flask-WTF global. Admin API uses `X-CSRFToken` header. Public API is CSRF-exempt.
- **Logout**: POST + CSRF, clears session.
- **CSP**: Talisman with strict policy. HSTS in production.
- **Proxy**: `ProxyFix` configured for Coolify (1 hop).
- **Passwords**: Argon2. Minimum 8 chars.
- **Media**: Type verified with Pillow (not file extension), EXIF orientation corrected, WebP conversion, SHA-256 checksum, SSRF-safe URL validation in imports.

## Data import

The legacy `data/db.json` can be imported into the database with:

```bash
flask import-wiki-data ../data/db.json [options]
```

Options:
- `--dry-run` — simulate without writing
- `--update-existing` — update articles found by slug
- `--publish` — publish valid articles after import
- `--continue-on-error` — keep going on individual errors
- `--download-images` — download external images to MinIO (not yet implemented)

Output: count of read, created, updated, skipped, errors, imported images.

## Documentation

- [`infraesructura.md`](infraesructura.md) — Architecture overview and diagrams
- [`IMPLEMENTATION_REPORT.md`](IMPLEMENTATION_REPORT.md) — Detailed list of all changes
- [`backend/README.md`](backend/README.md) — Backend specifics
- [`backend/Instructions.txt`](backend/Instructions.txt) — Deployment quick reference
