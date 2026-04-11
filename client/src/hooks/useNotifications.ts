/**
 * VisionX — Notification Hook
 * Subscribe to push notifications, manage notification state
 */

import { useCallback } from 'react';
import { create } from 'zustand';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'danger';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: { label: string; url: string };
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isOpen: boolean;
  addNotification: (n: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  togglePanel: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  notifications: [
    {
      id: '1', type: 'danger', title: 'Intrusion Detected',
      message: 'Person detected in Restricted Zone A',
      timestamp: new Date(Date.now() - 120000).toISOString(), read: false,
    },
    {
      id: '2', type: 'warning', title: 'Crowd Alert',
      message: 'Crowd threshold exceeded (>5 persons) in Main Entrance',
      timestamp: new Date(Date.now() - 300000).toISOString(), read: false,
    },
    {
      id: '3', type: 'success', title: 'Camera Connected',
      message: 'Camera_02 is now online and streaming',
      timestamp: new Date(Date.now() - 720000).toISOString(), read: true,
    },
  ],
  unreadCount: 2,
  isOpen: false,

  addNotification: (n) =>
    set((s) => {
      const notification: Notification = {
        ...n,
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        read: false,
      };
      return {
        notifications: [notification, ...s.notifications].slice(0, 100),
        unreadCount: s.unreadCount + 1,
      };
    }),

  markRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, s.unreadCount - (s.notifications.find((n) => n.id === id && !n.read) ? 1 : 0)),
    })),

  markAllRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, read: true })),
      unreadCount: 0,
    })),

  removeNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
      unreadCount: s.unreadCount - (s.notifications.find((n) => n.id === id && !n.read) ? 1 : 0),
    })),

  clearAll: () => set({ notifications: [], unreadCount: 0 }),
  togglePanel: () => set((s) => ({ isOpen: !s.isOpen })),
}));

export function useNotifications() {
  const store = useNotificationStore();

  const requestPermission = useCallback(async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  }, []);

  const showBrowserNotification = useCallback((title: string, body: string) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/favicon.svg' });
    }
  }, []);

  return { ...store, requestPermission, showBrowserNotification };
}
