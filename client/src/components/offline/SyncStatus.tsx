/**
 * VisionX — Sync Status Component
 * Shows sync progress when reconnecting after offline
 */

import { motion } from 'framer-motion';

interface SyncStatusProps {
  isSyncing: boolean;
  progress: number; // 0-100
  itemsLeft: number;
}

export function SyncStatus({ isSyncing, progress, itemsLeft }: SyncStatusProps) {
  if (!isSyncing) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        position: 'fixed', bottom: 24, right: 24, zIndex: 9998,
        padding: '16px 20px', borderRadius: 12, width: 260,
        background: 'rgba(15,15,25,0.95)', border: '1px solid var(--border)',
        backdropFilter: 'blur(20px)', boxShadow: '0 10px 40px rgba(0,0,0,0.4)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span className="text-sm font-medium">Syncing data...</span>
        <span className="text-xs mono" style={{ color: 'var(--accent)' }}>{progress}%</span>
      </div>
      <div style={{
        height: 4, borderRadius: 2, background: 'var(--surface)', overflow: 'hidden',
      }}>
        <motion.div
          style={{ height: '100%', borderRadius: 2, background: 'var(--accent)' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>
      <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 6 }}>
        {itemsLeft} items remaining
      </p>
    </motion.div>
  );
}
