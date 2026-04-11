/**
 * VisionX — Sidebar Layout Component
 */

import { motion } from 'framer-motion';
import { useAppStore, type AppMode } from '../../stores/appStore';
import { useThemeStore, THEMES } from '../../stores/themeStore';
import './Sidebar.css';

const NAV_ITEMS: { mode: AppMode; icon: string; label: string }[] = [
  { mode: 'monitoring', icon: '◉', label: 'Live Monitor' },
  { mode: 'analytics', icon: '◈', label: 'Analytics' },
  { mode: 'settings', icon: '⚙', label: 'Settings' },
  { mode: 'automation', icon: '⚡', label: 'Automation' },
  { mode: 'user', icon: '◎', label: 'My Dashboard' },
  { mode: 'help', icon: '?', label: 'Help Center' },
  { mode: 'admin', icon: '🛡', label: 'Admin' },
];

export function Sidebar() {
  const { mode, setMode, sidebarCollapsed, toggleSidebar } = useAppStore();
  const { theme, cycleTheme } = useThemeStore();
  const currentTheme = THEMES.find(t => t.id === theme)!;

  return (
    <motion.aside
      className={`sidebar ${sidebarCollapsed ? 'sidebar--collapsed' : ''}`}
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Logo */}
      <div className="sidebar__logo" onClick={toggleSidebar}>
        <span className="sidebar__logo-icon">◆</span>
        {!sidebarCollapsed && (
          <motion.span
            className="sidebar__logo-text"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            VisionX
          </motion.span>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <motion.button
            key={item.mode}
            className={`sidebar__nav-item ${mode === item.mode ? 'sidebar__nav-item--active' : ''}`}
            onClick={() => setMode(item.mode)}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.97 }}
          >
            <span className="sidebar__nav-icon">{item.icon}</span>
            {!sidebarCollapsed && <span className="sidebar__nav-label">{item.label}</span>}
            {mode === item.mode && (
              <motion.div
                className="sidebar__nav-indicator"
                layoutId="nav-indicator"
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
          </motion.button>
        ))}
      </nav>

      {/* Theme Switcher */}
      <div className="sidebar__footer">
        <motion.button
          className="sidebar__theme-btn"
          onClick={cycleTheme}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <span
            className="sidebar__theme-dot"
            style={{ background: currentTheme.accent }}
          />
          {!sidebarCollapsed && (
            <span className="sidebar__theme-name">{currentTheme.name}</span>
          )}
        </motion.button>
      </div>
    </motion.aside>
  );
}
