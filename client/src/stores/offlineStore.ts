/**
 * VisionX — Offline Store
 * Zustand: offline queue & sync state
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface QueuedAction {
  id: string;
  type: string;
  payload: any;
  timestamp: string;
}

interface OfflineState {
  isOnline: boolean;
  queue: QueuedAction[];
  isSyncing: boolean;
  syncProgress: number;
  lastSyncTime: string | null;
  setOnline: (isOnline: boolean) => void;
  addToQueue: (type: string, payload: any) => void;
  removeFromQueue: (id: string) => void;
  clearQueue: () => void;
  setSyncing: (isSyncing: boolean) => void;
  setSyncProgress: (progress: number) => void;
  setLastSyncTime: (time: string) => void;
}

export const useOfflineStore = create<OfflineState>()(
  persist(
    (set) => ({
      isOnline: true,
      queue: [],
      isSyncing: false,
      syncProgress: 0,
      lastSyncTime: null,

      setOnline: (isOnline) => set({ isOnline }),

      addToQueue: (type, payload) =>
        set((s) => ({
          queue: [...s.queue, {
            id: Date.now().toString(),
            type,
            payload,
            timestamp: new Date().toISOString(),
          }],
        })),

      removeFromQueue: (id) =>
        set((s) => ({ queue: s.queue.filter((q) => q.id !== id) })),

      clearQueue: () => set({ queue: [], syncProgress: 0 }),

      setSyncing: (isSyncing) => set({ isSyncing }),

      setSyncProgress: (syncProgress) => set({ syncProgress }),

      setLastSyncTime: (lastSyncTime) => set({ lastSyncTime }),
    }),
    { name: 'vx-offline' }
  )
);
