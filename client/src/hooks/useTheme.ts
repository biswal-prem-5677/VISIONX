/**
 * VisionX — useTheme Hook
 * Theme switching logic with DOM updates
 */

import { useCallback } from 'react';
import { useThemeStore, THEMES, type ThemeId } from '../stores/themeStore';

export function useTheme() {
  const { theme, setTheme, cycleTheme } = useThemeStore();

  const currentTheme = THEMES.find((t) => t.id === theme) || THEMES[0];

  const applyTheme = useCallback((themeId: ThemeId) => {
    setTheme(themeId);
    document.documentElement.setAttribute(
      'data-theme',
      themeId === 'obsidian' ? '' : themeId
    );
  }, [setTheme]);

  const isDark = true; // All themes are dark in VisionX

  return {
    theme,
    currentTheme,
    themes: THEMES,
    setTheme: applyTheme,
    cycleTheme,
    isDark,
  };
}
