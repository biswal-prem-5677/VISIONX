/**
 * VisionX — Character Store
 * ========================================
 * Zustand store for 3D AI character state management.
 * Controls archetype, expressions, idle state, gestures, and visibility.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type CharacterArchetype = 'guardian' | 'guide' | 'muse' | 'sage' | 'pilot';

export type Expression = 'neutral' | 'happy' | 'surprised' | 'concerned' | 'alert' | 'sleeping';

export type IdleState = 'active' | 'idle' | 'bored' | 'sleeping';

export type Gesture = 'none' | 'wave' | 'point' | 'thumbsUp' | 'alert' | 'thinking';

export interface CharacterConfig {
  archetype: CharacterArchetype;
  name: string;
  personality: string;
  primaryColor: string;
  secondaryColor: string;
  emissiveColor: string;
  particleColor: string;
}

export const CHARACTER_CONFIGS: Record<CharacterArchetype, CharacterConfig> = {
  guardian: {
    archetype: 'guardian',
    name: 'The Guardian',
    personality: 'Stoic, watchful, minimal gestures',
    primaryColor: '#1a1030',
    secondaryColor: '#6d28d9',
    emissiveColor: '#a78bfa',
    particleColor: '#8b5cf6',
  },
  guide: {
    archetype: 'guide',
    name: 'The Guide',
    personality: 'Energetic, encouraging, large gestures',
    primaryColor: '#0c2d48',
    secondaryColor: '#0ea5e9',
    emissiveColor: '#38bdf8',
    particleColor: '#7dd3fc',
  },
  muse: {
    archetype: 'muse',
    name: 'The Muse',
    personality: 'Ethereal, floating, follows cursor closely',
    primaryColor: '#0a1929',
    secondaryColor: '#06b6d4',
    emissiveColor: '#22d3ee',
    particleColor: '#67e8f9',
  },
  sage: {
    archetype: 'sage',
    name: 'The Sage',
    personality: 'Calm, meditative, slow breathing',
    primaryColor: '#052e16',
    secondaryColor: '#16a34a',
    emissiveColor: '#4ade80',
    particleColor: '#22c55e',
  },
  pilot: {
    archetype: 'pilot',
    name: 'The Pilot',
    personality: 'Tech-focused, sharp, precision movements',
    primaryColor: '#1c0a00',
    secondaryColor: '#ea580c',
    emissiveColor: '#fb923c',
    particleColor: '#f97316',
  },
};

export const THEME_TO_ARCHETYPE: Record<string, CharacterArchetype> = {
  obsidian: 'guardian',
  aurora: 'guide',
  cyber: 'muse',
  matrix: 'sage',
  ember: 'pilot',
};

interface CharacterState {
  archetype: CharacterArchetype;
  expression: Expression;
  idleState: IdleState;
  gesture: Gesture;
  visible: boolean;
  scale: number;
  lipSyncValue: number;
  lastInteractionTime: number;

  setArchetype: (archetype: CharacterArchetype) => void;
  setExpression: (expression: Expression) => void;
  setIdleState: (state: IdleState) => void;
  setGesture: (gesture: Gesture) => void;
  setVisible: (visible: boolean) => void;
  setScale: (scale: number) => void;
  setLipSyncValue: (value: number) => void;
  recordInteraction: () => void;
  getConfig: () => CharacterConfig;
}

export const useCharacterStore = create<CharacterState>()(
  persist(
    (set, get) => ({
      archetype: 'guardian',
      expression: 'neutral',
      idleState: 'active',
      gesture: 'none',
      visible: true,
      scale: 1,
      lipSyncValue: 0,
      lastInteractionTime: Date.now(),

      setArchetype: (archetype) => set({ archetype }),
      setExpression: (expression) => set({ expression }),
      setIdleState: (idleState) => set({ idleState }),
      setGesture: (gesture) => set({ gesture }),
      setVisible: (visible) => set({ visible }),
      setScale: (scale) => set({ scale }),
      setLipSyncValue: (value) => set({ lipSyncValue: value }),
      recordInteraction: () => set({ lastInteractionTime: Date.now(), idleState: 'active' }),
      getConfig: () => CHARACTER_CONFIGS[get().archetype],
    }),
    { name: 'visionx-character' }
  )
);
