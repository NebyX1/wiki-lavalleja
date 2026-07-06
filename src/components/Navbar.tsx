import { Link, NavLink } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

export default function Navbar() {
  return (
    <header className="wl-surface border-b wl-border sticky top-0 z-50">
      <div className="max-w-[1440px] mx-auto flex items-center justify-between h-14 px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 wl-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <div className="flex flex-col">
              <span className="wiki-page-title text-lg leading-tight">WikiLavalleja</span>
              <span className="hidden sm:block text-[10px] leading-tight wl-muted -mt-0.5">
                Archivo histórico-cultural de Minas y Lavalleja
              </span>
            </div>
          </Link>
        </div>

        <nav className="hidden md:flex items-center gap-1">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `px-3 py-1.5 rounded text-sm transition-colors ${
                isActive
                  ? "wl-surface-2 wl-accent font-medium"
                  : "wl-muted hover:wl-accent"
              }`
            }
          >
            Inicio
          </NavLink>
          <NavLink
            to="/#articulos"
            className={({ isActive }) =>
              `px-3 py-1.5 rounded text-sm transition-colors ${
                isActive
                  ? "wl-surface-2 wl-accent font-medium"
                  : "wl-muted hover:wl-accent"
              }`
            }
          >
            Artículos
          </NavLink>
        </nav>

        <div className="flex items-center gap-1">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
