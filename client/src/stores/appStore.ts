/**
 * VisionX — App Store
 * Global application state
 */

import { create } from 'zustand';

export type AppMode = 'monitoring' | 'analytics' | 'settings' | 'automation' | 'help' | 'admin' | 'user';

interface AppState {
  mode: AppMode;
  sidebarCollapsed: boolean;
  setMode: (mode: AppMode) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  mode: 'monitoring',
  sidebarCollapsed: false,

  setMode: (mode) => set({ mode }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
