/**
 * VisionX — Offline Banner Component
 * Shows "You are offline" indicator when internet disconnects
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useOffline } from '../../hooks/useOffline';

export function OfflineBanner() {
  const { isOnline, wasOffline, dismissReconnected } = useOffline();

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -40, opacity: 0 }}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10000,
            padding: '8px 16px', textAlign: 'center',
            background: 'linear-gradient(90deg, #dc2626, #ef4444)',
            color: '#fff', fontSize: '0.8rem', fontWeight: 600,
          }}
        >
          ⚠️ You are offline — VisionX is running in local mode. Data will sync when reconnected.
        </motion.div>
      )}

      {isOnline && wasOffline && (
        <motion.div
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -40, opacity: 0 }}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10000,
            padding: '8px 16px', textAlign: 'center',
            background: 'linear-gradient(90deg, #16a34a, #22c55e)',
            color: '#fff', fontSize: '0.8rem', fontWeight: 600,
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
          }}
        >
          ✅ Back online! Syncing data...
          <button
            onClick={dismissReconnected}
            style={{
              background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 4,
              color: '#fff', padding: '2px 8px', cursor: 'pointer', fontSize: '0.75rem',
            }}
          >
            Dismiss
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
