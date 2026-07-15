# IMPLEMENTATION REPORT — WikiLavalleja Full-Stack Integration

## Estado general

Se ha implementado la integración completa entre el frontend React y el backend Flask, transformando el boilerplate en un sistema de gestión y publicación de artículos enciclopédicos. El sistema está listo para desarrollo y despliegue.

## Modelos creados

- **Category** — Categorías de artículos (name, slug, description, sort_order, is_active)
- **Tag** — Etiquetas de artículos (name, slug)
- **Article** — Artículo enciclopédico completo con todos los campos del contrato
- **ArticleKeyFact** — Hechos destacados ordenables
- **ArticleTimelineEvent** — Eventos de cronología
- **ArticleRelatedPlace** — Lugares relacionados
- **ArticleSource** — Fuentes y referencias con validación de URL
- **MediaAsset** — Imágenes con UUID, variantes, metadatos EXIF, SHA-256
- **ArticleRevision** — Revisiones con snapshot JSON completo
- **article_tags** — Tabla de asociación many-to-many

## Migraciones creadas

- `0002_wiki_content_domain.py` — Crea todas las tablas del dominio wiki con índices y FKs. Reversible. No toca las tablas existentes (users, two_factor_codes, activity_logs).

## Endpoints públicos creados

- `GET /api/v1/articles` — Listado paginado con búsqueda, filtros y ordenamiento
- `GET /api/v1/articles/<slug>` — Detalle completo del artículo
- `GET /api/v1/categories` — Categorías activas con conteo de artículos
- `GET /api/v1/tags` — Etiquetas usadas en artículos publicados
- `GET /api/v1/media/<uuid>/content/<variant>` — Contenido multimedia (small/medium/large/original)
- `GET /api/v1/sitemap` — Sitemap XML dinámico

## Endpoints administrativos creados

- `GET/POST /api/v1/admin/articles` — Listado y creación
- `GET/PATCH/DELETE /api/v1/admin/articles/<id>` — CRUD
- `POST /api/v1/admin/articles/<id>/publish` — Publicar
- `POST /api/v1/admin/articles/<id>/unpublish` — Retirar publicación
- `POST /api/v1/admin/articles/<id>/archive` — Archivar
- `POST /api/v1/admin/articles/<id>/restore` — Restaurar
- `POST /api/v1/admin/articles/<id>/duplicate` — Duplicar
- `GET /api/v1/admin/articles/<id>/revisions` — Listar revisiones
- `POST /api/v1/admin/articles/<id>/revisions/<rev_id>/restore` — Restaurar revisión
- `POST /api/v1/admin/articles/<id>/autosave` — Autoguardado
- `GET/POST /api/v1/admin/categories` — CRUD de categorías
- `GET/POST /api/v1/admin/tags` — CRUD de etiquetas
- `GET/POST /api/v1/admin/media` — Listado y subida de imágenes
- `GET/PATCH/DELETE /api/v1/admin/media/<uuid>` — Gestión de imágenes
- `GET /api/v1/admin/media/<uuid>/usage` — Verificación de uso

## Pantallas administrativas creadas

- `/admin/articles` — Listado de artículos con filtros, búsqueda y paginación
- `/admin/articles/new` — Crear nuevo artículo con editor completo
- `/admin/articles/<id>/edit` — Editor de artículo con secciones: identidad, ficha, contenido, hechos, cronología, lugares, fuentes, imagen, publicación
- `/admin/articles/<id>/revisions` — Historial de revisiones
- `/admin/media` — Biblioteca multimedia con drag-and-drop
- Dashboard actualizado con métricas de artículos y multimedia

## Cambios en el frontend

- `src/lib/api.ts` — Reescrito para consumir Flask API en `/api/v1`, con tipos TypeScript, manejo de errores y paginación
- `src/types/article.ts` — Actualizado para reflejar el contrato del backend
- `src/pages/Home.tsx` — Búsqueda remota con debounce, paginación, filtros por categoría dinámica desde la API
- `src/pages/Articles.tsx` — Consume API Flask, SEO con react-helmet-async, Open Graph, Twitter Card
- `src/components/WikiSidebar.tsx` — Categorías dinámicas desde la API
- `src/components/ArticleCard.tsx` — Actualizado para nuevos tipos
- `src/components/ArticleInfobox.tsx` — Actualizado para nuevos tipos
- `src/main.tsx` — Añadido HelmetProvider para SEO
- JSON Server eliminado de package.json
- `.env.example` creado para el frontend

## Cambios de seguridad

- 2FA: código no se loguea a stdout salvo con `ENABLE_2FA_CODE_LOGGING=True`
- 2FA: incrementa `attempts` y invalida tras `MAX_2FA_ATTEMPTS`
- 2FA: invalida códigos anteriores al crear uno nuevo
- Logout: cambiado a POST con CSRF
- Session: `session.clear()` al completar 2FA (anti session fixation)
- ProxyFix configurado para Coolify
- CORS: solo endpoints públicos, sin credenciales
- CSRF: exento solo para API pública y admin API (que usan X-CSRFToken header)
- Entrypoint: detiene arranque si migración falla

## Comando de importación

```bash
cd backend
flask import-wiki-data ../data/db.json --publish --update-existing
```

## Resultado de build

- Frontend: `npm run build` — Compila correctamente
- Backend: Requiere `pip install -r requirements.txt` (añade Pillow)

## Limitaciones

- Las pruebas automatizadas (pytest, vitest, playwright) están pendientes de implementación
- El editor Markdown en el panel administrativo usa un textarea simple (EasyMDE no integrado aún)
- La descarga de imágenes remotas durante la importación no está implementada (--download-images no hace nada aún)
- OpenAPI/Swagger UI no está configurado
- El docker-compose.dev.yml no incluye el backend ni el frontend como servicios