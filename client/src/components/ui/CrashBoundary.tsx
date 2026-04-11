/**
 * VisionX — Error Boundary + Crash Reporter
 * Catches React render errors, shows fallback UI, reports to backend
 */

import React from 'react';
import { GlowButton } from './GlowButton';

interface Props {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class CrashBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });

    // Report to backend
    const report = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
    };

    // Queue locally
    try {
      const queue = JSON.parse(localStorage.getItem('vx_crash_queue') || '[]');
      queue.push(report);
      localStorage.setItem('vx_crash_queue', JSON.stringify(queue.slice(-50)));
    } catch { /* quota */ }

    // Try server
    fetch('/api/v1/crash-reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(report),
    }).catch(() => {});
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          minHeight: '100vh', background: 'var(--bg-primary, #0a0a0f)',
          color: 'var(--text-primary, #e4e4e7)', fontFamily: 'Inter, sans-serif',
          padding: 40,
        }}>
          <div style={{
            maxWidth: 480, textAlign: 'center',
            padding: 40, borderRadius: 16,
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            backdropFilter: 'blur(20px)',
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💥</div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }}>
              Something went wrong
            </h1>
            <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 24, lineHeight: 1.6 }}>
              VisionX encountered an unexpected error. The crash has been reported automatically.
            </p>
            {this.state.error && (
              <pre style={{
                textAlign: 'left', padding: 16, borderRadius: 8,
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
                fontSize: '0.75rem', overflow: 'auto', maxHeight: 120,
                color: '#f87171', marginBottom: 24,
              }}>
                {this.state.error.message}
              </pre>
            )}
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              <GlowButton onClick={this.handleReset}>Try Again</GlowButton>
              <GlowButton variant="ghost" onClick={() => window.location.reload()}>
                Reload Page
              </GlowButton>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
