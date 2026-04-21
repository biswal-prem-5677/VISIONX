/**
 * VisionX — Main Application
 * Mode-based page rendering · Theme Provider · Crash Boundary · Offline Support
 */

import { useEffect } from 'react';
import { useThemeStore } from './stores/themeStore';
import { useAppStore } from './stores/appStore';
import { useCrashReporter } from './hooks/useCrashReporter';
import { useStateRecovery } from './hooks/useStateRecovery';
import { useVisionStream } from './hooks/useVisionStream';

import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { CrashBoundary } from './components/ui/CrashBoundary';
import { CookieBanner } from './components/ui/CookieBanner';
import { NotificationPanel } from './components/notifications/NotificationPanel';
import { OfflineBanner } from './components/offline/OfflineBanner';

import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Automation from './pages/Automation';
import HelpCenter from './pages/HelpCenter';
import AdminDashboard from './pages/AdminDashboard';
import UserHome from './pages/UserHome';

import './index.css';
import './App.css';

function CurrentPage() {
  const mode = useAppStore((s) => s.mode);

  switch (mode) {
    case 'analytics':
      return <Analytics />;
    case 'settings':
      return <Settings />;
    case 'automation':
      return <Automation />;
    case 'help':
      return <HelpCenter />;
    case 'admin':
      return <AdminDashboard />;
    case 'user':
      return <UserHome />;
    default:
      return <Dashboard />;
  }
}

function App() {
  const theme = useThemeStore((s) => s.theme);
  const sidebarCollapsed = useAppStore((s) => s.sidebarCollapsed);

  // Initialize global crash reporter
  useCrashReporter();

  // Initialize WebSocket → Zustand store bridge
  useVisionStream();

  // Initialize state recovery (auto-save every 5s)
  const { restore } = useStateRecovery();
  useEffect(() => { restore(); }, [restore]);

  // Apply theme to DOM
  useEffect(() => {
    document.documentElement.setAttribute(
      'data-theme',
      theme === 'obsidian' ? '' : theme
    );
  }, [theme]);

  return (
    <CrashBoundary>
      <div className="app-layout">
        <Sidebar />
        <div className={`main-content ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <Header />
          <main className="page-container">
            <CurrentPage />
          </main>
        </div>

        {/* Global overlays */}
        <NotificationPanel />
        <OfflineBanner />
        <CookieBanner />
      </div>
    </CrashBoundary>
  );
}

export default App;
