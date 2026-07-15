import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getArticles, resolveMediaUrl, type ArticleSummary, type ArticleListResponse } from "../lib/api";
import SearchBox from "../components/SearchBox";

const portals = [
  { label: "Personajes históricos", icon: "👤", filter: "Independencia" },
  { label: "Literatura minuana", icon: "📖", filter: "Literatura" },
  { label: "Fundación de Minas", icon: "🏛️", filter: "Fundación de Minas" },
  { label: "Calles con memoria", icon: "🛣️", filter: "Independencia" },
  { label: "Lugares y monumentos", icon: "📍", filter: "Fundación de Minas" },
  { label: "Mujeres de Lavalleja", icon: "👩", filter: "Literatura y educación" },
];

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const catFilter = searchParams.get("cat") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading, isError, refetch } = useQuery<ArticleListResponse>({
    queryKey: ["articles", debouncedSearch, catFilter, page],
    queryFn: () => getArticles({
      q: debouncedSearch || undefined,
      category: catFilter || undefined,
      page,
      perPage: 12,
      sort: "newest",
    }),
  });

  const handlePageChange = useCallback((newPage: number) => {
    const params = new URLSearchParams(searchParams);
    if (newPage > 1) params.set("page", String(newPage));
    else params.delete("page");
    setSearchParams(params);
  }, [searchParams, setSearchParams]);

  const handleSearchChange = useCallback(() => {
    setSearchParams(prev => {
      prev.delete("page");
      return prev;
    });
  }, [setSearchParams]);

  const articles = data?.items || [];
  const pagination = data?.pagination;

  return (
    <div>
      <section className="relative h-48 md:h-56 overflow-hidden">
        <img
          src="https://commons.wikimedia.org/wiki/Special:FilePath/Minas%20Uruguay.jpg"
          alt="Vista de Minas, Uruguay"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 wl-hero-overlay" />
        <div className="absolute inset-0 flex items-center">
          <div className="px-6 lg:px-12 max-w-2xl">
            <div className="flex items-center gap-2 mb-2">
              <h1 className="wiki-page-title text-3xl md:text-4xl">WikiLavalleja</h1>
              <span className="badge badge-sm wl-accent wl-border">archivo vivo</span>
            </div>
            <p className="text-sm md:text-base wl-muted leading-relaxed max-w-xl">
              Una wiki simple para preservar personajes, calles, lugares y hechos de interés histórico-cultural de Lavalleja.
            </p>
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 lg:px-8 py-6">
        <div className="flex items-center gap-3 mb-6">
          <SearchBox
            value={search}
            onChange={(v) => { setSearch(v); handleSearchChange(); }}
            placeholder="Buscar por título, calle, categoría o etiqueta..."
            className="flex-1 max-w-md"
          />
          {catFilter && (
            <Link to="/" className="btn btn-ghost btn-xs gap-1">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Limpiar filtro
            </Link>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
          {portals.map((p) => {
            const href = `/?cat=${encodeURIComponent(p.filter)}`;
            return (
              <Link
                key={p.label}
                to={href}
                className={`wiki-card p-3 text-center hover:border-[var(--wl-accent)] transition-colors ${
                  catFilter === p.filter ? "ring-1 ring-[var(--wl-accent)]" : ""
                }`}
              >
                <span className="text-xl mb-1 block">{p.icon}</span>
                <span className="text-xs font-medium wl-muted leading-tight block">{p.label}</span>
              </Link>
            );
          })}
        </div>

        <div id="articulos" className="flex items-center justify-between mb-4">
          <h2 className="wiki-page-title text-xl">
            {catFilter ? `Categoría: ${catFilter}` : "Todos los artículos"}
          </h2>
          <span className="text-xs wl-muted">{pagination?.total || 0} artículos</span>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="wiki-card">
                <div className="skeleton h-40 w-full rounded-t-lg" />
                <div className="p-4 space-y-2">
                  <div className="skeleton h-3 w-16" />
                  <div className="skeleton h-5 w-3/4" />
                  <div className="skeleton h-3 w-1/2" />
                  <div className="skeleton h-4 w-full" />
                  <div className="skeleton h-4 w-2/3" />
                </div>
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="text-center py-12" aria-live="polite">
            <p className="wl-muted text-lg mb-4">No se pudo conectar con el servidor.</p>
            <button onClick={() => refetch()} className="btn btn-primary btn-sm">Reintentar</button>
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-16">
            <p className="wl-muted text-lg">
              No se encontraron artículos{debouncedSearch ? ` para "${debouncedSearch}"` : ""}.
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>

            {pagination && pagination.pages > 1 && (
              <nav className="flex items-center justify-center gap-2 mt-8" aria-label="Paginación">
                {pagination.hasPrevious && (
                  <button onClick={() => handlePageChange(page - 1)} className="px-3 py-1 text-sm border wl-border rounded-lg hover:wl-surface-2">
                    Anterior
                  </button>
                )}
                <span className="text-sm wl-muted">Página {pagination.page} de {pagination.pages}</span>
                {pagination.hasNext && (
                  <button onClick={() => handlePageChange(page + 1)} className="px-3 py-1 text-sm border wl-border rounded-lg hover:wl-surface-2">
                    Siguiente
                  </button>
                )}
              </nav>
            )}
          </>
        )}
      </section>
    </div>
  );
}

function ArticleCard({ article }: { article: ArticleSummary }) {
  const heroImage = article.heroImage ? resolveMediaUrl(article.heroImage) : null;
  return (
    <article className="wiki-card group">
      <Link to={`/articulos/${article.slug}`} className="block">
        <div className="relative h-40 overflow-hidden">
          {heroImage && (
            <img
              src={heroImage}
              alt={article.imageAlt || ""}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
          )}
          <span className="absolute top-2 left-2 badge badge-sm wl-surface wl-border font-medium">
            {article.category?.name || "Sin categoría"}
          </span>
        </div>
      </Link>
      <div className="p-4">
        <Link to={`/articulos/${article.slug}`}>
          <h3 className="wiki-page-title text-base mb-1 line-clamp-2 group-hover:wl-accent transition-colors">
            {article.title}
          </h3>
        </Link>
        <p className="text-xs italic wl-muted mb-2 line-clamp-1">{article.subtitle || ""}</p>
        <p className="text-sm line-clamp-2 mb-3 leading-relaxed" style={{ color: "var(--wl-muted)" }}>
          {article.summary || ""}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-xs wl-muted flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {article.streetName || ""}
          </span>
          <Link to={`/articulos/${article.slug}`} className="text-xs font-medium wl-accent hover:opacity-80 transition-colors">
            Leer artículo →
          </Link>
        </div>
      </div>
    </article>
  );
}