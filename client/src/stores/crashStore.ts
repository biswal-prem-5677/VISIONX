/**
 * VisionX — Crash Store
 * Zustand: crash recovery state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface CrashInfo {
  message: string;
  stack?: string;
  timestamp: string;
  recovered: boolean;
}

interface CrashState {
  crashes: CrashInfo[];
  lastCrash: CrashInfo | null;
  totalCrashes: number;
  addCrash: (crash: Omit<CrashInfo, 'recovered'>) => void;
  markRecovered: () => void;
  clearCrashes: () => void;
}

export const useCrashStore = create<CrashState>()(
  persist(
    (set) => ({
      crashes: [],
      lastCrash: null,
      totalCrashes: 0,

      addCrash: (crash) =>
        set((s) => {
          const info: CrashInfo = { ...crash, recovered: false };
          return {
            crashes: [info, ...s.crashes].slice(0, 50),
            lastCrash: info,
            totalCrashes: s.totalCrashes + 1,
          };
        }),

      markRecovered: () =>
        set((s) => ({
          lastCrash: s.lastCrash ? { ...s.lastCrash, recovered: true } : null,
        })),

      clearCrashes: () => set({ crashes: [], lastCrash: null }),
    }),
    { name: 'vx-crashes' }
  )
);
