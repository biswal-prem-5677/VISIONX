/**
 * VisionX — Offline Banner Component
 * Shows "You are offline" indicator when internet disconnects
 * Includes manual reconnect button for WebSocket recovery
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useOffline } from '../../hooks/useOffline';
import { useVisionStore } from '../../stores/visionStore';

export function OfflineBanner() {
  const { isOnline, wasOffline, dismissReconnected } = useOffline();
  const isProcessing = useVisionStore((s) => s.isProcessing);

  // Show reconnect option when online but WebSocket is dead
  const wsDisconnected = isOnline && !isProcessing;

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
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
          }}
        >
          ⚠️ You are offline — VisionX is running in local mode. Data will sync when reconnected.
          <button
            onClick={() => window.location.reload()}
            style={{
              background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: 4,
              color: '#fff', padding: '2px 10px', cursor: 'pointer', fontSize: '0.75rem',
            }}
          >
            ↻ Retry
          </button>
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

      {wsDisconnected && !wasOffline && (
        <motion.div
          initial={{ y: -40, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -40, opacity: 0 }}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10000,
            padding: '8px 16px', textAlign: 'center',
            background: 'linear-gradient(90deg, #d97706, #f59e0b)',
            color: '#fff', fontSize: '0.8rem', fontWeight: 600,
            display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12,
          }}
        >
          ⚡ Vision stream disconnected — live feed paused
          <button
            onClick={() => window.location.reload()}
            style={{
              background: 'rgba(255,255,255,0.25)', border: 'none', borderRadius: 4,
              color: '#fff', padding: '4px 12px', cursor: 'pointer', fontSize: '0.75rem',
              fontWeight: 600,
            }}
          >
            ↻ Reconnect
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
