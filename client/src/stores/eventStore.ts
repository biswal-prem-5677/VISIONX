/**
 * VisionX — Event Store
 * Alert and event state from decision/event engines
 */

import { create } from 'zustand';

export interface VisionEvent {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'danger';
  message: string;
  camera: string;
  timestamp: string;
  acknowledged: boolean;
}

interface EventState {
  events: VisionEvent[];
  activeAlerts: number;
  addEvent: (event: Omit<VisionEvent, 'id' | 'timestamp' | 'acknowledged'>) => void;
  acknowledgeEvent: (id: string) => void;
  clearEvents: () => void;
}

export const useEventStore = create<EventState>((set) => ({
  events: [],
  activeAlerts: 0,

  addEvent: (event) =>
    set((s) => {
      const newEvent: VisionEvent = {
        ...event,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        acknowledged: false,
      };
      const events = [newEvent, ...s.events].slice(0, 500);
      return {
        events,
        activeAlerts: events.filter((e) => !e.acknowledged && e.severity !== 'info').length,
      };
    }),

  acknowledgeEvent: (id) =>
    set((s) => {
      const events = s.events.map((e) => e.id === id ? { ...e, acknowledged: true } : e);
      return {
        events,
        activeAlerts: events.filter((e) => !e.acknowledged && e.severity !== 'info').length,
      };
    }),

  clearEvents: () => set({ events: [], activeAlerts: 0 }),
}));
