/**
 * VisionX — Theme Store
 * Zustand store for theme management
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeName = 'obsidian' | 'cyber' | 'aurora' | 'ember' | 'matrix';

export interface ThemeInfo {
  id: ThemeName;
  name: string;
  accent: string;
  description: string;
  character: string;
  characterName: string;
}

export const THEMES: ThemeInfo[] = [
  { id: 'obsidian', name: 'Obsidian', accent: '#a78bfa', description: 'Deep purple elegance', character: 'guardian', characterName: 'The Guardian' },
  { id: 'cyber', name: 'Cyber Neon', accent: '#00e5ff', description: 'Futuristic cyan glow', character: 'muse', characterName: 'The Muse' },
  { id: 'aurora', name: 'Aurora', accent: '#38bdf8', description: 'Northern lights blue', character: 'guide', characterName: 'The Guide' },
  { id: 'ember', name: 'Ember', accent: '#fb923c', description: 'Warm fire orange', character: 'pilot', characterName: 'The Pilot' },
  { id: 'matrix', name: 'Matrix', accent: '#22c55e', description: 'Digital green rain', character: 'sage', characterName: 'The Sage' },
];

interface ThemeState {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
  cycleTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'obsidian',

      setTheme: (theme: ThemeName) => {
        document.documentElement.setAttribute('data-theme', theme === 'obsidian' ? '' : theme);
        set({ theme });
      },

      cycleTheme: () => {
        const current = get().theme;
        const idx = THEMES.findIndex(t => t.id === current);
        const next = THEMES[(idx + 1) % THEMES.length];
        get().setTheme(next.id);
      },
    }),
    { name: 'visionx-theme' }
  )
);
