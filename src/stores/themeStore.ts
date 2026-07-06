import { create } from "zustand";

export type ThemeMode = "light" | "dark";

interface ThemeState {
  theme: ThemeMode;
  initialized: boolean;
  initializeTheme: () => void;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
}

const STORAGE_KEY = "wikilavalleja-theme";

function applyTheme(theme: ThemeMode) {
  if (typeof window === "undefined") return;
  const root = document.documentElement;

  if (theme === "dark") {
    root.classList.add("dark");
    root.setAttribute("data-theme", "night");
    root.style.colorScheme = "dark";
  } else {
    root.classList.remove("dark");
    root.setAttribute("data-theme", "light");
    root.style.colorScheme = "light";
  }

  localStorage.setItem(STORAGE_KEY, theme);
}

function getSystemPreference(): ThemeMode {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function getStoredTheme(): ThemeMode | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  return null;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: "light",
  initialized: false,

  initializeTheme: () => {
    const stored = getStoredTheme();
    const theme = stored ?? getSystemPreference();
    applyTheme(theme);
    set({ theme, initialized: true });
  },

  setTheme: (theme: ThemeMode) => {
    applyTheme(theme);
    set({ theme });
  },

  toggleTheme: () => {
    const next: ThemeMode = useThemeStore.getState().theme === "light" ? "dark" : "light";
    applyTheme(next);
    set({ theme: next });
  },
}));
