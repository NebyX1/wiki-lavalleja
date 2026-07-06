import { useThemeStore } from "../stores/themeStore";

export default function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggleTheme);

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="wl-theme-button inline-flex h-10 w-10 items-center justify-center rounded-full border transition relative z-[9999] cursor-pointer"
      aria-label={theme === "light" ? "Activar modo nocturno" : "Activar modo diurno"}
      title={theme === "light" ? "Modo oscuro" : "Modo claro"}
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
