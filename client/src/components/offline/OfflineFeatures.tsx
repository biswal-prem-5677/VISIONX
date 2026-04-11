/**
 * VisionX — OfflineFeatures Component
 * Shows which features are available offline
 */

import { motion } from 'framer-motion';

interface OfflineFeature {
  name: string;
  available: boolean;
  description: string;
}

const FEATURES: OfflineFeature[] = [
  { name: 'Live Detection', available: true, description: 'Edge AI runs locally — no cloud needed' },
  { name: 'Local Recording', available: true, description: 'Save video clips to local storage' },
  { name: 'Alert History', available: true, description: 'View recent cached alerts' },
  { name: 'Settings', available: true, description: 'Modify local configuration' },
  { name: 'Analytics', available: false, description: 'Requires server for historical data' },
  { name: 'Cloud Modules', available: false, description: 'Face/OCR/Pose need cloud compute' },
  { name: 'Notifications', available: false, description: 'Push/email require network' },
  { name: 'User Management', available: false, description: 'Admin features need server' },
];

export function OfflineFeatures() {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Available Offline</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {FEATURES.map((f, i) => (
          <motion.div
            key={f.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-subtle"
            style={{
              padding: '12px 14px', borderRadius: 'var(--radius-sm)',
              opacity: f.available ? 1 : 0.5,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 14 }}>{f.available ? '✅' : '❌'}</span>
              <span className="font-medium text-sm">{f.name}</span>
            </div>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{f.description}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
