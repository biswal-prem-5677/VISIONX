/**
 * VisionX — Notification Panel Component
 * Dropdown panel showing all notifications with actions
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useNotificationStore } from '../../hooks/useNotifications';

const TYPE_ICONS: Record<string, string> = {
  info: '🔵', success: '🟢', warning: '🟡', danger: '🔴',
};

function timeAgo(timestamp: string): string {
  const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export function NotificationPanel() {
  const { notifications, isOpen, markRead, markAllRead, removeNotification, clearAll, togglePanel } =
    useNotificationStore();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 998 }}
            onClick={togglePanel}
          />
          {/* Panel */}
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            style={{
              position: 'fixed', top: 56, right: 16, width: 380, maxHeight: 500,
              zIndex: 999, borderRadius: 16, overflow: 'hidden',
              background: 'rgba(15,15,25,0.98)', border: '1px solid var(--border)',
              backdropFilter: 'blur(20px)', boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
            }}
          >
            {/* Header */}
            <div style={{
              padding: '16px 20px', borderBottom: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <span className="font-semibold">Notifications</span>
              <div style={{ display: 'flex', gap: 12 }}>
                <button onClick={markAllRead} className="text-xs"
                  style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}>
                  Mark all read
                </button>
                <button onClick={clearAll} className="text-xs"
                  style={{ color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}>
                  Clear
                </button>
              </div>
            </div>

            {/* List */}
            <div style={{ overflowY: 'auto', maxHeight: 420 }}>
              {notifications.length === 0 ? (
                <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  <div style={{ fontSize: 32, marginBottom: 8 }}>🔔</div>
                  <p className="text-sm">No notifications</p>
                </div>
              ) : (
                notifications.map((n) => (
                  <motion.div
                    key={n.id}
                    layout
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    onClick={() => markRead(n.id)}
                    style={{
                      padding: '14px 20px', cursor: 'pointer',
                      borderBottom: '1px solid var(--border)',
                      background: n.read ? 'transparent' : 'rgba(var(--accent-rgb, 139,92,246), 0.05)',
                      transition: 'background 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                      <span style={{ fontSize: 14, marginTop: 2 }}>{TYPE_ICONS[n.type]}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span className="font-medium text-sm">{n.title}</span>
                          <button
                            onClick={(e) => { e.stopPropagation(); removeNotification(n.id); }}
                            style={{
                              background: 'none', border: 'none', cursor: 'pointer',
                              color: 'var(--text-tertiary)', fontSize: 12,
                            }}
                          >
                            ✕
                          </button>
                        </div>
                        <p className="text-xs" style={{ color: 'var(--text-secondary)', marginTop: 2 }}>
                          {n.message}
                        </p>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4, display: 'block' }}>
                          {timeAgo(n.timestamp)}
                        </span>
                      </div>
                    </div>
                    {!n.read && (
                      <div style={{
                        position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)',
                        width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)',
                      }} />
                    )}
                  </motion.div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
