import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Helmet } from "react-helmet-async";
import { getArticleBySlug, resolveMediaUrl, type ArticleDetail } from "../lib/api";
import ArticleInfobox from "../components/ArticleInfobox";
import MarkdownContent from "../components/MarkdownContent";
import WikiToc from "../components/WikiToc";
import { extractToc } from "../lib/utils";
import type { Article } from "../types/article";

function adaptArticle(detail: ArticleDetail): Article {
  return {
    id: detail.id,
    slug: detail.slug,
    title: detail.title,
    subtitle: detail.subtitle,
    type: detail.type,
    streetName: detail.streetName,
    period: detail.period,
    birthPlace: detail.birthPlace,
    deathPlace: detail.deathPlace,
    category: detail.category,
    tags: detail.tags,
    summary: detail.summary,
    heroImage: detail.heroImage ? resolveMediaUrl(detail.heroImage) : null,
    heroMedia: detail.heroMedia,
    imageAlt: detail.imageAlt,
    imageCredit: detail.imageCredit,
    coordinates: detail.coordinates as Article["coordinates"],
    streetEvidence: detail.streetEvidence as Article["streetEvidence"],
    historicalContext: detail.historicalContext,
    keyFacts: detail.keyFacts,
    timeline: detail.timeline,
    relatedPlaces: detail.relatedPlaces,
    sources: detail.sources as Article["sources"],
    sourceNotes: detail.sourceNotes,
    body: detail.body,
    status: detail.status,
    featured: detail.featured,
    publishedAt: detail.publishedAt,
    updatedAt: detail.updatedAt,
    seo: detail.seo,
  };
}

export default function Articles() {
  const { slug } = useParams<{ slug: string }>();

  const { data: detail, isLoading, error } = useQuery<ArticleDetail | null>({
    queryKey: ["article", slug],
    queryFn: () => getArticleBySlug(slug!),
    enabled: !!slug,
  });

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 lg:px-8 py-8">
        <div className="skeleton h-4 w-48 mb-6" />
        <div className="skeleton h-8 w-1/2 mb-2" />
        <div className="skeleton h-5 w-1/3 mb-4" />
        <div className="skeleton h-64 w-full rounded-lg mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-3">
            <div className="skeleton h-4 w-full" />
            <div className="skeleton h-4 w-5/6" />
            <div className="skeleton h-4 w-full" />
            <div className="skeleton h-4 w-3/4" />
          </div>
          <div className="skeleton h-64 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-4 lg:px-8 py-8">
        <div className="alert alert-error max-w-lg" aria-live="polite">
          <div>
            <p className="font-bold">Error de conexión</p>
            <p className="text-sm">No se pudo cargar el artículo. Verificá que el servidor esté funcionando.</p>
          </div>
        </div>
        <Link to="/" className="btn btn-ghost btn-sm mt-4">← Volver al inicio</Link>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="max-w-5xl mx-auto px-4 lg:px-8 py-8">
        <div className="text-center py-16">
          <h1 className="wiki-page-title text-3xl mb-3">Artículo no encontrado</h1>
          <p className="wl-muted mb-6">Este artículo todavía no existe en WikiLavalleja.</p>
          <Link to="/" className="btn btn-primary btn-sm">Volver al inicio</Link>
        </div>
      </div>
    );
  }

  const article = adaptArticle(detail);
  const tocItems = extractToc(article.body || "");
  const heroImage = article.heroImage;

  return (
    <div className="max-w-5xl mx-auto px-4 lg:px-8 py-6">
      <Helmet>
        <title>{article.seo?.title || article.title} - WikiLavalleja</title>
        {article.seo?.description && <meta name="description" content={article.seo.description} />}
        {article.seo?.canonicalUrl && <link rel="canonical" href={article.seo.canonicalUrl} />}
        {heroImage && <meta property="og:image" content={heroImage} />}
        <meta property="og:title" content={article.seo?.title || article.title} />
        {article.seo?.description && <meta property="og:description" content={article.seo.description} />}
        <meta property="og:type" content="article" />
        <meta name="twitter:card" content="summary_large_image" />
      </Helmet>

      <nav className="text-xs wl-muted mb-4 flex items-center gap-1">
        <Link to="/" className="hover:wl-accent transition-colors">Inicio</Link>
        <span>/</span>
        <span style={{ color: "var(--wl-muted)" }}>{article.title}</span>
      </nav>

      <div className="mb-4">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          {article.category && <span className="badge badge-sm wl-accent wl-border">{article.category.name}</span>}
          {article.type && <span className="badge badge-sm badge-outline">{article.type}</span>}
        </div>
        <h1 className="wiki-page-title text-2xl md:text-3xl mb-1">{article.title}</h1>
        <p className="text-base italic wl-muted">{article.subtitle}</p>
      </div>

      <div className="flex flex-wrap gap-3 text-xs wl-muted mb-5 pb-4 border-b wl-border">
        {article.period && <span className="flex items-center gap-1">📅 {article.period}</span>}
        {article.streetName && <span className="flex items-center gap-1">📍 {article.streetName}</span>}
        {article.birthPlace && <span className="flex items-center gap-1">🏠 {article.birthPlace}</span>}
      </div>

      <figure className="mb-6 rounded-lg overflow-hidden border wl-border">
        {heroImage && (
          <img src={heroImage} alt={article.imageAlt || ""} className="w-full h-48 md:h-64 object-cover" />
        )}
        <figcaption className="text-[11px] wl-muted px-3 py-1.5 wl-surface-2">
          {article.imageCredit || ""}
        </figcaption>
      </figure>

      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr_300px] gap-6">
        <aside className="hidden lg:block">
          <div className="sticky top-20">
            <WikiToc items={tocItems} />
          </div>
        </aside>

        <article id="contenido" className="min-w-0">
          {article.historicalContext && (
            <section className="mt-8 p-4 wl-surface-2 rounded-lg border wl-border">
              <h3 className="text-sm font-semibold wl-muted uppercase tracking-wider mb-2">Contexto histórico</h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--wl-muted)" }}>{article.historicalContext}</p>
            </section>
          )}

          <MarkdownContent content={article.body || ""} />

          {article.keyFacts.length > 0 && (
            <section className="mt-8">
              <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Datos clave</h2>
              <ul className="space-y-2">
                {article.keyFacts.map((fact, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm leading-relaxed" style={{ color: "var(--wl-muted)" }}>
                    <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: "var(--wl-sepia, #c9a96e)" }} />
                    {fact}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {article.timeline.length > 0 && (
            <section className="mt-8">
              <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Línea de tiempo</h2>
              <div className="relative pl-6">
                <div className="absolute left-2 top-1 bottom-1 w-px" style={{ background: "var(--wl-border)" }} />
                <div className="space-y-4">
                  {article.timeline.map((item, i) => (
                    <div key={i} className="relative">
                      <span className="absolute -left-6 top-1 w-4 h-4 rounded-full wl-accent border-2" style={{ background: "var(--wl-accent-soft)", borderColor: "var(--wl-accent)" }} />
                      <div>
                        <span className="text-xs font-bold wl-accent">{item.year}</span>
                        <p className="text-sm leading-relaxed" style={{ color: "var(--wl-muted)" }}>{item.event}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {article.relatedPlaces.length > 0 && (
            <section className="mt-8">
              <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Lugares relacionados</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {article.relatedPlaces.map((place, i) => (
                  <div key={i} className="wl-card rounded-lg p-3">
                    <span className="badge badge-xs wl-accent wl-border">{place.type}</span>
                    <h4 className="text-sm font-semibold mt-1">{place.name}</h4>
                    <p className="text-xs wl-muted leading-relaxed">{place.description}</p>
                  </div>
                ))}
              </div>
            </section>
          )}

          {article.sources.length > 0 && (
            <section className="mt-8">
              <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Fuentes y referencias</h2>
              <ol className="space-y-2 list-decimal list-inside text-sm wl-muted">
                {article.sources.map((src, i) => (
                  <li key={i} className="leading-relaxed">
                    <a href={src.url} target="_blank" rel="noopener noreferrer" className="wl-accent underline underline-offset-2 hover:opacity-80">
                      {src.label}
                    </a>
                    <span className="ml-1 text-xs wl-muted">({src.kind})</span>
                  </li>
                ))}
              </ol>
              {article.sourceNotes && (
                <div className="mt-4 p-3 wl-surface-2 rounded-lg border wl-border text-xs wl-muted leading-relaxed">
                  <strong>Nota:</strong> {article.sourceNotes}
                </div>
              )}
            </section>
          )}
        </article>

        <aside className="hidden lg:block">
          <div className="sticky top-20">
            <ArticleInfobox article={article} />
          </div>
        </aside>
      </div>

      <div className="mt-10 mb-8">
        <Link to="/" className="btn btn-ghost btn-sm gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Volver a todos los artículos
        </Link>
      </div>
    </div>
  );
}