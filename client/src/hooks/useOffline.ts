/**
 * VisionX — Offline Detection Hook
 * Monitors network status and provides offline state
 */

import { useState, useEffect, useCallback } from 'react';

interface OfflineState {
  isOnline: boolean;
  wasOffline: boolean;
  lastOnline: Date | null;
  downtime: number; // seconds
}

export function useOffline() {
  const [state, setState] = useState<OfflineState>({
    isOnline: navigator.onLine,
    wasOffline: false,
    lastOnline: navigator.onLine ? new Date() : null,
    downtime: 0,
  });

  const handleOnline = useCallback(() => {
    setState((s) => ({
      isOnline: true,
      wasOffline: true,
      lastOnline: new Date(),
      downtime: s.lastOnline ? Math.floor((Date.now() - s.lastOnline.getTime()) / 1000) : 0,
    }));
  }, []);

  const handleOffline = useCallback(() => {
    setState((s) => ({
      ...s,
      isOnline: false,
      lastOnline: s.lastOnline || new Date(),
    }));
  }, []);

  const dismissReconnected = useCallback(() => {
    setState((s) => ({ ...s, wasOffline: false }));
  }, []);

  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  return { ...state, dismissReconnected };
}
