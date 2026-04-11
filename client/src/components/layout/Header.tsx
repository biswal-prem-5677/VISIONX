/**
 * VisionX — Header Layout Component
 */

import { motion } from 'framer-motion';
import { useAppStore } from '../../stores/appStore';
import { useNotificationStore } from '../../hooks/useNotifications';
import './Header.css';

const MODE_LABELS: Record<string, string> = {
  monitoring: 'Live Monitoring',
  analytics: 'Analytics Dashboard',
  settings: 'Configuration',
  automation: 'Automation Rules',
  help: 'Help Center',
  admin: 'Admin Dashboard',
  user: 'My Dashboard',
};

export function Header() {
  const { mode, sidebarCollapsed } = useAppStore();
  const { unreadCount, togglePanel } = useNotificationStore();

  return (
    <header className={`header ${sidebarCollapsed ? 'header--expanded' : ''}`}>
      <div className="header__left">
        <motion.h1
          className="header__title"
          key={mode}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          {MODE_LABELS[mode]}
        </motion.h1>
      </div>

      <div className="header__right">
        {/* Live Status */}
        <div className="header__status">
          <span className="header__status-dot" />
          <span className="header__status-text">System Active</span>
        </div>

        {/* Notification Bell */}
        <motion.button
          className="header__icon-btn"
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          aria-label="Notifications"
          onClick={togglePanel}
        >
          🔔
          {unreadCount > 0 && (
            <span className="header__badge">{unreadCount}</span>
          )}
        </motion.button>

        {/* User Avatar */}
        <div className="header__avatar">
          <span>A</span>
        </div>
      </div>
    </header>
  );
}
