import { useEffect } from "react";
import { useThemeStore } from "../stores/themeStore";

export default function ThemeInitializer() {
  const initializeTheme = useThemeStore((s) => s.initializeTheme);
  const initialized = useThemeStore((s) => s.initialized);

  useEffect(() => {
    if (!initialized) {
      initializeTheme();
    }
  }, [initializeTheme, initialized]);

  return null;
}
