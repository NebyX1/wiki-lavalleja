import { useState } from "react";
import type { TocItem } from "../lib/utils";

interface WikiTocProps {
  items: TocItem[];
}

export default function WikiToc({ items }: WikiTocProps) {
  const [collapsed, setCollapsed] = useState(false);

  if (items.length === 0) return null;

  return (
    <div className="wiki-toc">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-between w-full px-4 py-3 text-sm font-semibold wl-muted hover:wl-accent transition-colors"
        aria-expanded={!collapsed}
      >
        <span className="uppercase tracking-wider text-xs">Contenido</span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-4 w-4 transition-transform ${collapsed ? "-rotate-90" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {!collapsed && (
        <nav className="px-3 pb-3" aria-label="Tabla de contenidos">
          {items.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              className={item.level === 3 ? "toc-h3" : ""}
            >
              {item.text}
            </a>
          ))}
        </nav>
      )}
    </div>
  );
}
