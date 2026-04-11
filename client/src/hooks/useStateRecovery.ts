/**
 * VisionX — State Recovery Hook
 * Auto-saves app state to localStorage, restores on reload/crash
 */

import { useEffect, useCallback } from 'react';
import { useAppStore } from '../stores/appStore';
import { useThemeStore } from '../stores/themeStore';

const STATE_KEY = 'vx_state_snapshot';
const SAVE_INTERVAL = 5000; // 5 seconds

interface StateSnapshot {
  mode: string;
  sidebarCollapsed: boolean;
  theme: string;
  timestamp: string;
  scrollPosition: number;
}

export function useStateRecovery() {
  // Save state periodically
  useEffect(() => {
    const save = () => {
      const { mode, sidebarCollapsed } = useAppStore.getState();
      const { theme } = useThemeStore.getState();

      const snapshot: StateSnapshot = {
        mode,
        sidebarCollapsed,
        theme,
        timestamp: new Date().toISOString(),
        scrollPosition: window.scrollY,
      };

      try {
        localStorage.setItem(STATE_KEY, JSON.stringify(snapshot));
      } catch { /* quota exceeded */ }
    };

    const interval = setInterval(save, SAVE_INTERVAL);

    // Also save on page hide (tab close, navigate away)
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') save();
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', save);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', save);
    };
  }, []);

  // Restore state on mount
  const restore = useCallback(() => {
    try {
      const raw = localStorage.getItem(STATE_KEY);
      if (!raw) return null;

      const snapshot: StateSnapshot = JSON.parse(raw);
      const { setMode } = useAppStore.getState();
      const { setTheme } = useThemeStore.getState();

      setMode(snapshot.mode as any);
      if (snapshot.sidebarCollapsed !== useAppStore.getState().sidebarCollapsed) {
        useAppStore.getState().toggleSidebar();
      }
      setTheme(snapshot.theme as any);

      // Restore scroll after a tick
      requestAnimationFrame(() => {
        window.scrollTo(0, snapshot.scrollPosition);
      });

      return snapshot;
    } catch {
      return null;
    }
  }, []);

  return { restore };
}
