import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getArticles } from "../lib/api";
import type { Article } from "../types/article";
import ArticleCard from "../components/ArticleCard";
import SearchBox from "../components/SearchBox";

const portals = [
  { label: "Personajes históricos", icon: "👤", filter: "Independencia" },
  { label: "Literatura minuana", icon: "📖", filter: "Literatura" },
  { label: "Fundación de Minas", icon: "🏛️", filter: "Fundación de Minas" },
  { label: "Calles con memoria", icon: "🛣️", category: "Independencia" },
  { label: "Lugares y monumentos", icon: "📍", category: "Fundación de Minas" },
  { label: "Mujeres de Lavalleja", icon: "👩", filter: "Literatura y educación" },
];

export default function Home() {
  const [searchParams] = useSearchParams();
  const catFilter = searchParams.get("cat") || "";
  const [search, setSearch] = useState("");

  const { data: articles = [], isLoading } = useQuery<Article[]>({
    queryKey: ["articles"],
    queryFn: getArticles,
  });

  const filtered = articles.filter((a) => {
    const matchesSearch = !search.trim() || (() => {
      const q = search.toLowerCase();
      return (
        a.title.toLowerCase().includes(q) ||
        a.subtitle.toLowerCase().includes(q) ||
        a.streetName.toLowerCase().includes(q) ||
        a.category.toLowerCase().includes(q) ||
        a.tags.some((t) => t.toLowerCase().includes(q))
      );
    })();
    const matchesCategory = !catFilter || a.category === catFilter;
    return matchesSearch && matchesCategory;
  });

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
              <span className="badge badge-sm wl-accent wl-border">
                archivo vivo
              </span>
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
            onChange={setSearch}
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
            const href = p.filter
              ? `/?cat=${encodeURIComponent(p.filter)}`
              : p.category
              ? `/?cat=${encodeURIComponent(p.category)}`
              : "/";
            return (
              <Link
                key={p.label}
                to={href}
                className={`wiki-card p-3 text-center hover:border-[var(--wl-accent)] transition-colors ${
                  catFilter === (p.filter || p.category) ? "ring-1 ring-[var(--wl-accent)]" : ""
                }`}
              >
                <span className="text-xl mb-1 block">{p.icon}</span>
                <span className="text-xs font-medium wl-muted leading-tight block">
                  {p.label}
                </span>
              </Link>
            );
          })}
        </div>

        <div id="articulos" className="flex items-center justify-between mb-4">
          <h2 className="wiki-page-title text-xl">
            {catFilter ? `Categoría: ${catFilter}` : "Todos los artículos"}
          </h2>
          <span className="text-xs wl-muted">{filtered.length} artículos</span>
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
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <p className="wl-muted text-lg">
              No se encontraron artículos{search ? ` para "${search}"` : ""}.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filtered.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
