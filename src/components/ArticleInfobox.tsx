import type { Article } from "../types/article";

interface ArticleInfoboxProps {
  article: Article;
}

export default function ArticleInfobox({ article }: ArticleInfoboxProps) {
  return (
    <div className="wiki-infobox">
      <figure className="border-b wl-border">
        <img
          src={article.heroImage}
          alt={article.imageAlt}
          className="w-full object-cover max-h-56"
        />
      </figure>
      <div className="p-0">
        <h2 className="wiki-page-title text-base px-3 pt-3 pb-2">{article.title}</h2>
        <dl>
          <dt>Tipo</dt>
          <dd>{article.type}</dd>

          <dt>Período</dt>
          <dd>{article.period}</dd>

          <dt>Nacimiento</dt>
          <dd>{article.birthPlace}</dd>

          {article.deathPlace && (
            <>
              <dt>Fallecimiento</dt>
              <dd>{article.deathPlace}</dd>
            </>
          )}

          <dt>Calle</dt>
          <dd>{article.streetName}</dd>

          <dt>Categoría</dt>
          <dd>{article.category}</dd>

          {article.coordinates && (
            <>
              <dt>Coordenadas</dt>
              <dd>
                {article.coordinates.lat != null && article.coordinates.lng != null
                  ? `${article.coordinates.lat.toFixed(4)}, ${article.coordinates.lng.toFixed(4)}`
                  : "No disponibles"}
                <span className="block text-[10px] wl-muted mt-0.5">
                  Precisión: {article.coordinates.confidence}
                </span>
              </dd>
            </>
          )}
        </dl>

        {article.tags.length > 0 && (
          <div className="px-3 pb-2">
            <dt className="text-xs font-semibold wl-muted uppercase tracking-wider mb-1.5">Etiquetas</dt>
            <div className="flex flex-wrap gap-1">
              {article.tags.map((tag) => (
                <span key={tag} className="badge badge-outline badge-xs">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {article.sources && article.sources.length > 0 && (
          <div className="px-3 pb-2">
            <dt className="text-xs font-semibold wl-muted uppercase tracking-wider mb-1">
              Fuentes
            </dt>
            <dd className="text-xs wl-muted">{article.sources.length} referencias</dd>
          </div>
        )}

        <p className="text-[10px] wl-muted px-3 pb-3 leading-relaxed">
          Crédito imagen: {article.imageCredit}
        </p>
      </div>
    </div>
  );
}
