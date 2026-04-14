/**
 * VisionX — NotificationToast Component
 * Floating toast alerts for real-time events
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Toast {
  id: string;
  type: 'info' | 'success' | 'warning' | 'danger';
  title: string;
  message: string;
  duration?: number;
}

const TYPE_STYLES = {
  info: { bg: 'rgba(56,189,248,0.1)', border: '#38bdf8', icon: 'ℹ️' },
  success: { bg: 'rgba(34,197,94,0.1)', border: '#22c55e', icon: '✅' },
  warning: { bg: 'rgba(251,191,36,0.1)', border: '#fbbf24', icon: '⚠️' },
  danger: { bg: 'rgba(248,113,113,0.1)', border: '#f87171', icon: '🔴' },
};

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Date.now().toString();
    setToasts((t) => [...t, { ...toast, id }]);
    setTimeout(() => {
      setToasts((t) => t.filter((tt) => tt.id !== id));
    }, toast.duration || 5000);
  };

  const removeToast = (id: string) => {
    setToasts((t) => t.filter((tt) => tt.id !== id));
  };

  return { toasts, addToast, removeToast };
}

export function NotificationToast({ toasts, onDismiss }: {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 10001,
      display: 'flex', flexDirection: 'column', gap: 8, width: 340,
    }}>
      <AnimatePresence>
        {toasts.map((toast) => {
          const style = TYPE_STYLES[toast.type];
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: 100, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 100, scale: 0.9 }}
              transition={{ type: 'spring', damping: 25 }}
              style={{
                padding: '14px 16px', borderRadius: 12,
                background: 'rgba(15,15,25,0.97)', border: `1px solid var(--border)`,
                backdropFilter: 'blur(20px)', boxShadow: '0 10px 30px rgba(0,0,0,0.4)',
                borderLeft: `4px solid ${style.border}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', gap: 10 }}>
                  <span>{style.icon}</span>
                  <div>
                    <span className="font-medium text-sm">{toast.title}</span>
                    <p className="text-xs" style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                      {toast.message}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => onDismiss(toast.id)}
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--text-tertiary)', fontSize: 14,
                  }}
                >
                  ✕
                </button>
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
