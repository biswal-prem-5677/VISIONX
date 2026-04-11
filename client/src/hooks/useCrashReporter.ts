/**
 * VisionX — Crash Reporter Hook
 * Captures uncaught errors and reports them to the backend
 */

import { useEffect, useCallback } from 'react';

interface CrashReport {
  message: string;
  stack?: string;
  componentStack?: string;
  url: string;
  timestamp: string;
  userAgent: string;
  appVersion: string;
}

const CRASH_ENDPOINT = '/api/v1/crash-reports';
const APP_VERSION = '1.0.0';

export function useCrashReporter() {
  const reportCrash = useCallback(async (report: CrashReport) => {
    // Store locally first (offline-safe)
    try {
      const existing = JSON.parse(localStorage.getItem('vx_crash_queue') || '[]');
      existing.push(report);
      localStorage.setItem('vx_crash_queue', JSON.stringify(existing.slice(-50)));
    } catch { /* quota exceeded */ }

    // Try sending to server
    try {
      await fetch(CRASH_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(report),
      });
    } catch { /* server unreachable — queued locally */ }
  }, []);

  const createReport = useCallback((error: Error, componentStack?: string): CrashReport => ({
    message: error.message,
    stack: error.stack,
    componentStack,
    url: window.location.href,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    appVersion: APP_VERSION,
  }), []);

  // Global error handler
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      const report = createReport(new Error(event.message));
      report.stack = `${event.filename}:${event.lineno}:${event.colno}`;
      reportCrash(report);
    };

    const handleRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason instanceof Error
        ? event.reason
        : new Error(String(event.reason));
      reportCrash(createReport(error));
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleRejection);

    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleRejection);
    };
  }, [reportCrash, createReport]);

  // Flush queued reports on mount
  useEffect(() => {
    const flush = async () => {
      try {
        const queue = JSON.parse(localStorage.getItem('vx_crash_queue') || '[]');
        if (queue.length === 0) return;

        await fetch(CRASH_ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reports: queue }),
        });
        localStorage.removeItem('vx_crash_queue');
      } catch { /* will retry next load */ }
    };
    flush();
  }, []);

  return { reportCrash, createReport };
}
