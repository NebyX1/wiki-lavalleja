# WikiLavalleja - JSON Server

Este proyecto usa JSON Server como backend dummy para desarrollo y testing del frontend.

## Archivo de datos

La base dummy está en:

```bash
data/db.json
```

Contiene una colección `articles` con 5 artículos de ejemplo sobre Minas, Lavalleja.

## Cómo iniciar

En una terminal, ejecutar:

```bash
npm run server
```

Esto levanta JSON Server en el puerto 3001 con watching automático:

```
json-server --watch data/db.json --port 3001
```

## Endpoints disponibles

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `http://localhost:3001/articles` | Lista todos los artículos |
| GET | `http://localhost:3001/articles?slug=juan-antonio-lavalleja` | Filtra por slug |
| GET | `http://localhost:3001/articles/juan-antonio-lavalleja` | Obtiene un artículo por ID |

## Estructura de un artículo

Cada artículo incluye campos básicos (id, slug, title, body) y campos enriquecidos:

- `coordinates` — Coordenadas geográficas con nivel de confianza
- `streetEvidence` — Estado de verificación de la calle en el nomenclátor
- `historicalContext` — Contexto histórico del personaje o hecho
- `keyFacts` — Lista de datos clave
- `timeline` — Línea de tiempo con año y evento
- `relatedPlaces` — Lugares relacionados
- `sources` — Fuentes consultadas con tipo y URL
- `sourceNotes` — Notas sobre fuentes pendientes
- `body` — Contenido en Markdown

## Notas

- JSON Server soporta filtrado por query string: `/articles?category=Independencia`
- El frontend consume estos endpoints vía Axios + TanStack Query
- No requiere autenticación
- Ideal para desarrollo local y demos
