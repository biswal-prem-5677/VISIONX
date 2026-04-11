/**
 * VisionX — EventHistory Component
 * Past event browser with severity filtering
 */

import { useState } from 'react';
import { motion } from 'framer-motion';

interface HistoryEvent {
  id: number;
  type: string;
  camera: string;
  time: string;
  severity: 'info' | 'warning' | 'danger';
}

interface EventHistoryProps {
  events: HistoryEvent[];
  title?: string;
}

export function EventHistory({ events, title = 'Recent Events' }: EventHistoryProps) {
  const [filter, setFilter] = useState<'all' | 'danger' | 'warning' | 'info'>('all');

  const filtered = filter === 'all' ? events : events.filter((e) => e.severity === filter);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 className="font-semibold">{title}</h3>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['all', 'danger', 'warning', 'info'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="text-xs"
              style={{
                padding: '4px 10px', borderRadius: 'var(--radius-sm)',
                background: filter === f ? 'var(--accent)' : 'var(--surface)',
                color: filter === f ? '#fff' : 'var(--text-secondary)',
                border: 'none', cursor: 'pointer', textTransform: 'capitalize',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {filtered.map((e) => (
          <motion.div
            key={e.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-subtle"
            style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
            }}
          >
            <div>
              <span className={`badge badge-${e.severity}`} style={{ marginRight: 10, fontSize: '0.55rem' }}>
                {e.severity === 'danger' ? '🔴' : e.severity === 'warning' ? '🟡' : '🔵'}
              </span>
              <span className="font-medium text-sm">{e.type}</span>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{e.camera}</span>
              <span className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginLeft: 12 }}>{e.time}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
