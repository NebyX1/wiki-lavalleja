import { Link } from "react-router-dom";

interface WikiSidebarProps {
  className?: string;
}

const categories = [
  { label: "Personajes históricos", filter: "Independencia" },
  { label: "Literatura minuana", filter: "Literatura" },
  { label: "Fundación de Minas", filter: "Fundación de Minas" },
  { label: "Calles con memoria", hash: "#calles" },
  { label: "Lugares y monumentos", hash: "#lugares" },
  { label: "Mujeres de Lavalleja", filter: "Literatura y educación" },
];

export default function WikiSidebar({ className = "" }: WikiSidebarProps) {
  return (
    <aside className={`wiki-sidebar ${className}`}>
      <nav className="space-y-1" aria-label="Navegación principal">
        <Link to="/" className="wiki-sidebar-link">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Inicio
        </Link>
        <Link to="/" className="wiki-sidebar-link">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          Artículos
        </Link>

        <hr className="wiki-section-divider my-3" />

        <p className="text-xs font-semibold uppercase tracking-wider wl-muted px-3 pt-1 pb-2">
          Categorías
        </p>
        {categories.map((cat) => (
          <Link
            key={cat.label}
            to={cat.filter ? `/?cat=${encodeURIComponent(cat.filter)}` : cat.hash ? `/${cat.hash}` : "/"}
            className="wiki-sidebar-link text-sm"
          >
            <span className="w-1.5 h-1.5 rounded-full wl-accent shrink-0" style={{ opacity: 0.5 }} />
            {cat.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
