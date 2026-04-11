/**
 * VisionX — NotificationBell Component
 * Header bell icon with live badge count
 */

import { motion } from 'framer-motion';
import { useNotificationStore } from '../../hooks/useNotifications';

export function NotificationBell() {
  const { unreadCount, togglePanel } = useNotificationStore();

  return (
    <motion.button
      className="header__icon-btn"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      aria-label="Notifications"
      onClick={togglePanel}
      style={{
        position: 'relative', background: 'none', border: 'none',
        cursor: 'pointer', fontSize: 18, padding: 6,
      }}
    >
      🔔
      {unreadCount > 0 && (
        <motion.span
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          style={{
            position: 'absolute', top: -2, right: -4,
            width: 18, height: 18, borderRadius: '50%',
            background: 'var(--danger)', color: '#fff',
            fontSize: '0.6rem', fontWeight: 700,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          {unreadCount > 9 ? '9+' : unreadCount}
        </motion.span>
      )}
    </motion.button>
  );
}
