/**
 * VisionX — AlertPanel Component
 * Live alert notifications feed
 */

import { motion, AnimatePresence } from 'framer-motion';

export interface Alert {
  id: number;
  type: string;
  message: string;
  time: string;
  severity: 'info' | 'warning' | 'danger';
}

interface AlertPanelProps {
  alerts: Alert[];
  onDismiss?: (id: number) => void;
}

const SEVERITY_COLORS = {
  danger: { bg: 'rgba(248,113,113,0.1)', border: '#f87171', icon: '🔴' },
  warning: { bg: 'rgba(251,191,36,0.1)', border: '#fbbf24', icon: '🟡' },
  info: { bg: 'rgba(56,189,248,0.1)', border: '#38bdf8', icon: '🔵' },
};

export function AlertPanel({ alerts, onDismiss }: AlertPanelProps) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Recent Alerts</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <AnimatePresence>
          {alerts.map((alert) => {
            const style = SEVERITY_COLORS[alert.severity];
            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                style={{
                  padding: '12px 14px', borderRadius: 'var(--radius-sm)',
                  background: style.bg, borderLeft: `3px solid ${style.border}`,
                  cursor: onDismiss ? 'pointer' : 'default',
                }}
                onClick={() => onDismiss?.(alert.id)}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>{style.icon}</span>
                  <span className="font-medium text-sm">{alert.message}</span>
                </div>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4, display: 'block', paddingLeft: 24 }}>
                  {alert.time}
                </span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
