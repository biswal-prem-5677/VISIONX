/**
 * VisionX — EventLog Component
 * Automation execution log
 */

import { motion } from 'framer-motion';

interface LogEntry {
  id: number;
  ruleName: string;
  trigger: string;
  action: string;
  status: 'success' | 'failed' | 'pending';
  timestamp: string;
}

interface EventLogProps {
  entries: LogEntry[];
}

const STATUS_STYLES = {
  success: { color: '#22c55e', bg: 'rgba(34,197,94,0.1)', icon: '✅' },
  failed: { color: '#f87171', bg: 'rgba(248,113,113,0.1)', icon: '❌' },
  pending: { color: '#fbbf24', bg: 'rgba(251,191,36,0.1)', icon: '⏳' },
};

export function EventLog({ entries }: EventLogProps) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Execution Log</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 400, overflowY: 'auto' }}>
        {entries.length === 0 ? (
          <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <p className="text-sm">No executions yet</p>
          </div>
        ) : (
          entries.map((entry) => {
            const s = STATUS_STYLES[entry.status];
            return (
              <motion.div
                key={entry.id}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                style={{
                  padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                  background: s.bg, borderLeft: `3px solid ${s.color}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="text-sm">
                    {s.icon} <strong>{entry.ruleName}</strong>
                  </span>
                  <span className="text-xs mono" style={{ color: 'var(--text-tertiary)' }}>
                    {entry.timestamp}
                  </span>
                </div>
                <div className="text-xs" style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
                  {entry.trigger} → {entry.action}
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
