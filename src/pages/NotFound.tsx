import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="max-w-5xl mx-auto px-4 lg:px-8 py-16 text-center">
      <p className="text-6xl font-serif wl-muted mb-4" style={{ opacity: 0.2 }}>404</p>
      <h1 className="wiki-page-title text-2xl mb-2">Artículo no encontrado</h1>
      <p className="wl-muted mb-6 max-w-md mx-auto">
        Este artículo todavía no existe en WikiLavalleja.
      </p>
      <Link to="/" className="btn btn-primary btn-sm">Volver al inicio</Link>
    </div>
  );
}
