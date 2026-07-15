import { Link } from "react-router-dom";
import type { Article } from "../types/article";

interface ArticleCardProps {
  article: Article;
}

export default function ArticleCard({ article }: ArticleCardProps) {
  return (
    <article className="wiki-card group">
      <Link to={`/articulos/${article.slug}`} className="block">
        <div className="relative h-40 overflow-hidden">
          {article.heroImage && (
            <img
              src={article.heroImage}
              alt={article.imageAlt ?? ""}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
              loading="lazy"
            />
          )}
          <span className="absolute top-2 left-2 badge badge-sm wl-surface wl-border font-medium">
            {article.category?.name ?? "Sin categoría"}
          </span>
        </div>
      </Link>
      <div className="p-4">
        <Link to={`/articulos/${article.slug}`}>
          <h3 className="wiki-page-title text-base mb-1 line-clamp-2 group-hover:wl-accent transition-colors">
            {article.title}
          </h3>
        </Link>
        <p className="text-xs italic wl-muted mb-2 line-clamp-1">{article.subtitle ?? ""}</p>
        <p className="text-sm line-clamp-2 mb-3 leading-relaxed" style={{ color: "var(--wl-muted)" }}>
          {article.summary ?? ""}
        </p>
        <div className="flex items-center justify-between">
          <span className="text-xs wl-muted flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {article.streetName ?? ""}
          </span>
          <Link to={`/articulos/${article.slug}`} className="text-xs font-medium wl-accent hover:opacity-80 transition-colors">
            Leer artículo →
          </Link>
        </div>
      </div>
    </article>
  );
}