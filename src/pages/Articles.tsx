import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getArticleBySlug } from "../lib/api";
import type { Article } from "../types/article";
import ArticleInfobox from "../components/ArticleInfobox";
import MarkdownContent from "../components/MarkdownContent";
import WikiToc from "../components/WikiToc";
import { extractToc } from "../lib/utils";

function TimelineSection({ timeline }: { timeline: Article["timeline"] }) {
  if (!timeline || timeline.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Línea de tiempo</h2>
      <div className="relative pl-6">
        <div className="absolute left-2 top-1 bottom-1 w-px" style={{ background: "var(--wl-border)" }} />
        <div className="space-y-4">
          {timeline.map((item, i) => (
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
  );
}

function KeyFactsSection({ facts }: { facts: Article["keyFacts"] }) {
  if (!facts || facts.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Datos clave</h2>
      <ul className="space-y-2">
        {facts.map((fact, i) => (
          <li key={i} className="flex items-start gap-2 text-sm leading-relaxed" style={{ color: "var(--wl-muted)" }}>
            <span className="w-1.5 h-1.5 rounded-full mt-2 shrink-0" style={{ background: "var(--wl-sepia, #c9a96e)" }} />
            {fact}
          </li>
        ))}
      </ul>
    </section>
  );
}

function RelatedPlacesSection({ places }: { places: Article["relatedPlaces"] }) {
  if (!places || places.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Lugares relacionados</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {places.map((place, i) => (
          <div key={i} className="wl-card rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className="badge badge-xs wl-accent wl-border">{place.type}</span>
            </div>
            <h4 className="text-sm font-semibold">{place.name}</h4>
            <p className="text-xs wl-muted leading-relaxed">{place.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function SourcesSection({ sources, sourceNotes }: { sources: Article["sources"]; sourceNotes?: string }) {
  if (!sources || sources.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="wiki-page-title text-xl pb-2 border-b wl-border mb-4">Fuentes y referencias</h2>
      <ol className="space-y-2 list-decimal list-inside text-sm wl-muted">
        {sources.map((src, i) => (
          <li key={i} className="leading-relaxed">
            <a
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="wl-accent underline underline-offset-2 hover:opacity-80"
            >
              {src.label}
            </a>
            <span className="ml-1 text-xs wl-muted">({src.kind})</span>
          </li>
        ))}
      </ol>
      {sourceNotes && (
        <div className="mt-4 p-3 wl-surface-2 rounded-lg border wl-border text-xs wl-muted leading-relaxed">
          <strong>Nota:</strong> {sourceNotes}
        </div>
      )}
    </section>
  );
}

function HistoricalContextSection({ context }: { context: string }) {
  if (!context) return null;
  return (
    <section className="mt-8 p-4 wl-surface-2 rounded-lg border wl-border">
      <h3 className="text-sm font-semibold wl-muted uppercase tracking-wider mb-2">Contexto histórico</h3>
      <p className="text-sm leading-relaxed" style={{ color: "var(--wl-muted)" }}>{context}</p>
    </section>
  );
}

export default function Articles() {
  const { slug } = useParams<{ slug: string }>();

  const { data: article, isLoading, error } = useQuery<Article | null>({
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
        <div className="alert alert-error max-w-lg">
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="font-bold">Error al cargar el artículo</p>
            <p className="text-sm">No se pudo conectar con la base dummy. Verificá que JSON Server esté corriendo en http://localhost:3001.</p>
          </div>
        </div>
        <Link to="/" className="btn btn-ghost btn-sm mt-4">← Volver al inicio</Link>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="max-w-5xl mx-auto px-4 lg:px-8 py-8">
        <div className="text-center py-16">
          <h1 className="wiki-page-title text-3xl mb-3">Artículo no encontrado</h1>
          <p className="wl-muted mb-6">
            Este artículo todavía no existe en WikiLavalleja.
          </p>
          <Link to="/" className="btn btn-primary btn-sm">Volver al inicio</Link>
        </div>
      </div>
    );
  }

  const tocItems = extractToc(article.body);

  return (
    <div className="max-w-5xl mx-auto px-4 lg:px-8 py-6">
      <nav className="text-xs wl-muted mb-4 flex items-center gap-1">
        <Link to="/" className="hover:wl-accent transition-colors">Inicio</Link>
        <span>/</span>
        <span style={{ color: "var(--wl-muted)" }}>{article.title}</span>
      </nav>

      <div className="mb-4">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="badge badge-sm wl-accent wl-border">{article.category}</span>
          <span className="badge badge-sm badge-outline">{article.type}</span>
        </div>
        <h1 className="wiki-page-title text-2xl md:text-3xl mb-1">{article.title}</h1>
        <p className="text-base italic wl-muted">{article.subtitle}</p>
      </div>

      <div className="flex flex-wrap gap-3 text-xs wl-muted mb-5 pb-4 border-b wl-border">
        <span className="flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          {article.period}
        </span>
        <span className="flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          {article.streetName}
        </span>
        <span className="flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
          {article.birthPlace}
        </span>
      </div>

      <figure className="mb-6 rounded-lg overflow-hidden border wl-border">
        <img
          src={article.heroImage}
          alt={article.imageAlt}
          className="w-full h-48 md:h-64 object-cover"
        />
        <figcaption className="text-[11px] wl-muted px-3 py-1.5 wl-surface-2">
          {article.imageCredit}
        </figcaption>
      </figure>

      <div className="flex items-center gap-4 text-xs wl-muted mb-6 pb-4 border-b wl-border overflow-x-auto">
        <a href="#contenido" className="pb-2 border-b-2 border-[var(--wl-accent)] wl-accent font-medium whitespace-nowrap">Artículo</a>
        {article.sources && article.sources.length > 0 && (
          <a href="#fuentes-y-referencias" className="pb-2 border-b-2 border-transparent hover:border-[var(--wl-border)] whitespace-nowrap transition-colors">Fuentes</a>
        )}
        {article.relatedPlaces && article.relatedPlaces.length > 0 && (
          <a href="#lugares-relacionados" className="pb-2 border-b-2 border-transparent hover:border-[var(--wl-border)] whitespace-nowrap transition-colors">Lugares</a>
        )}
        {article.timeline && article.timeline.length > 0 && (
          <a href="#linea-de-tiempo" className="pb-2 border-b-2 border-transparent hover:border-[var(--wl-border)] whitespace-nowrap transition-colors">Línea de tiempo</a>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr_300px] gap-6">
        <aside className="hidden lg:block">
          <div className="sticky top-20">
            <WikiToc items={tocItems} />
          </div>
        </aside>

        <article id="contenido" className="min-w-0">
          <HistoricalContextSection context={article.historicalContext} />
          <MarkdownContent content={article.body} />
          <KeyFactsSection facts={article.keyFacts} />
          <TimelineSection timeline={article.timeline} />
          <RelatedPlacesSection places={article.relatedPlaces} />
          <SourcesSection sources={article.sources} sourceNotes={article.sourceNotes} />
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
