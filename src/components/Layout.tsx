import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import WikiSidebar from "./WikiSidebar";

export default function Layout() {
  return (
    <div className="wl-app min-h-screen">
      <Navbar />
      <div className="max-w-[1440px] mx-auto flex">
        <WikiSidebar className="hidden lg:block w-[220px] shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto p-4 border-r wl-border wl-surface" />
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
      <footer className="border-t wl-border wl-surface">
        <div className="max-w-[1440px] mx-auto px-4 lg:px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs wl-muted">
          <p>WikiLavalleja — Archivo histórico-cultural de Minas y Lavalleja</p>
          <p>Proyecto de demostración · Datos de ejemplo</p>
        </div>
      </footer>
    </div>
  );
}
