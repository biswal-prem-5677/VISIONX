/**
 * VisionX — NotificationPrefs Component
 * User notification preference settings
 */

import { useState } from 'react';
import { motion } from 'framer-motion';

interface Pref {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

const DEFAULT_PREFS: Pref[] = [
  { id: 'push', label: 'Push Notifications', description: 'Browser push alerts for critical events', enabled: true },
  { id: 'email', label: 'Email Alerts', description: 'Receive email for danger-level events', enabled: true },
  { id: 'sound', label: 'Sound Alerts', description: 'Play audio for new alerts', enabled: false },
  { id: 'crowd', label: 'Crowd Alerts', description: 'Notify when person count exceeds threshold', enabled: true },
  { id: 'intrusion', label: 'Intrusion Alerts', description: 'Notify on restricted zone violations', enabled: true },
  { id: 'camera', label: 'Camera Status', description: 'Notify when cameras go offline', enabled: true },
];

export function NotificationPrefs({ onSave }: { onSave?: (prefs: Pref[]) => void }) {
  const [prefs, setPrefs] = useState(DEFAULT_PREFS);

  const toggle = (id: string) => {
    const updated = prefs.map((p) => p.id === id ? { ...p, enabled: !p.enabled } : p);
    setPrefs(updated);
    onSave?.(updated);
  };

  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Notification Preferences</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {prefs.map((p) => (
          <div key={p.id} className="glass-subtle" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '12px 14px', borderRadius: 'var(--radius-sm)',
          }}>
            <div>
              <span className="font-medium text-sm">{p.label}</span>
              <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>{p.description}</span>
            </div>
            <motion.button
              onClick={() => toggle(p.id)}
              whileTap={{ scale: 0.9 }}
              style={{
                width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                background: p.enabled ? 'var(--accent)' : 'var(--surface)',
                position: 'relative',
              }}
            >
              <motion.div
                style={{ width: 18, height: 18, borderRadius: '50%', background: '#fff', position: 'absolute', top: 3 }}
                animate={{ left: p.enabled ? 23 : 3 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              />
            </motion.button>
          </div>
        ))}
      </div>
    </div>
  );
}
