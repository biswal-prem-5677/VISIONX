/**
 * VisionX — Admin Dashboard Page (God Mode)
 * System-wide view: users, health, crashes, usage, config
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

const systemStats = [
  { label: 'Total Users', value: '1,247', change: '+23', icon: '👥', color: '#a78bfa' },
  { label: 'Active Now', value: '89', change: '+12', icon: '🟢', color: '#22c55e' },
  { label: 'API Calls/min', value: '3.2K', change: '+8%', icon: '⚡', color: '#38bdf8' },
  { label: 'Crash Rate', value: '0.02%', change: '-0.01%', icon: '💥', color: '#f87171' },
];

const mockUsers = [
  { id: 1, name: 'John Smith', email: 'john@acme.com', plan: 'Enterprise', status: 'active', cameras: 8, lastActive: '2 min ago' },
  { id: 2, name: 'Sara Chen', email: 'sara@startup.io', plan: 'Pro', status: 'active', cameras: 3, lastActive: '15 min ago' },
  { id: 3, name: 'Mike Johnson', email: 'mike@retail.co', plan: 'Free', status: 'active', cameras: 1, lastActive: '1 hour ago' },
  { id: 4, name: 'Lisa Park', email: 'lisa@security.com', plan: 'Enterprise', status: 'suspended', cameras: 12, lastActive: '3 days ago' },
  { id: 5, name: 'Tom Wilson', email: 'tom@factory.com', plan: 'Pro', status: 'active', cameras: 5, lastActive: '30 min ago' },
];

const crashReports = [
  { id: 1, error: 'WebSocket timeout on live feed', count: 23, users: 8, severity: 'medium', lastSeen: '1h ago' },
  { id: 2, error: 'YOLO model load failure (OOM)', count: 5, users: 3, severity: 'high', lastSeen: '3h ago' },
  { id: 3, error: 'Stripe webhook signature invalid', count: 2, users: 1, severity: 'low', lastSeen: '1d ago' },
];

export default function AdminDashboard() {
  const [selectedTab, setSelectedTab] = useState<'users' | 'health' | 'crashes' | 'usage'>('users');

  return (
    <div className="admin-dashboard">
      {/* Admin Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 className="text-2xl font-bold" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: 'var(--danger)' }}>🛡️</span> God Mode
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
            Full system control — handle with care
          </p>
        </div>
        <span className="badge badge-danger" style={{ padding: '6px 12px' }}>ADMIN</span>
      </div>

      {/* System Stats */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        {systemStats.map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <GlassCard className="stat-card">
              <div className="stat-card__icon" style={{ color: stat.color }}>{stat.icon}</div>
              <div className="stat-card__info">
                <span className="stat-card__value">{stat.value}</span>
                <span className="stat-card__label">{stat.label}</span>
              </div>
              <span className="badge badge-success" style={{ marginLeft: 'auto', fontSize: '0.65rem' }}>{stat.change}</span>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, background: 'var(--surface)', borderRadius: 'var(--radius-md)', padding: 4 }}>
        {(['users', 'health', 'crashes', 'usage'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            style={{
              flex: 1, padding: '10px 16px', borderRadius: 'var(--radius-sm)',
              background: selectedTab === tab ? 'var(--accent)' : 'transparent',
              color: selectedTab === tab ? '#fff' : 'var(--text-secondary)',
              border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
              fontFamily: 'var(--font-sans)', transition: 'all 0.2s',
              textTransform: 'capitalize',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {selectedTab === 'users' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <GlassCard>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 className="font-semibold">All Users ({mockUsers.length})</h3>
              <input
                type="text" placeholder="Search users..."
                style={{
                  padding: '6px 12px', borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {mockUsers.map((user) => (
                <div key={user.id} className="glass-subtle" style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: '50%', background: 'var(--accent)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '0.8rem', fontWeight: 700, color: '#fff',
                    }}>
                      {user.name[0]}
                    </div>
                    <div>
                      <span className="font-medium text-sm">{user.name}</span>
                      <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>{user.email}</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className={`badge ${user.plan === 'Enterprise' ? 'badge-warning' : user.plan === 'Pro' ? 'badge-accent' : 'badge-info'}`}
                      style={{ fontSize: '0.6rem' }}>{user.plan}</span>
                    <span className="text-xs mono">{user.cameras} cam</span>
                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{user.lastActive}</span>
                    <GlowButton variant="ghost" size="sm">View</GlowButton>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      )}

      {selectedTab === 'crashes' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Crash Reports</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {crashReports.map((crash) => (
                <div key={crash.id} className="glass-subtle" style={{
                  padding: '14px 16px', borderRadius: 'var(--radius-sm)',
                  borderLeft: `3px solid ${crash.severity === 'high' ? 'var(--danger)' : crash.severity === 'medium' ? 'var(--warning)' : 'var(--info)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="font-medium text-sm">{crash.error}</span>
                    <span className={`badge badge-${crash.severity === 'high' ? 'danger' : crash.severity === 'medium' ? 'warning' : 'info'}`}>
                      {crash.severity}
                    </span>
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 6 }}>
                    {crash.count} occurrences · {crash.users} users affected · Last seen {crash.lastSeen}
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      )}

      {(selectedTab === 'health' || selectedTab === 'usage') && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <GlassCard>
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>{selectedTab === 'health' ? '💚' : '📊'}</div>
              <h3 className="font-semibold">{selectedTab === 'health' ? 'System Health' : 'Usage Analytics'}</h3>
              <p className="text-sm" style={{ marginTop: 8 }}>
                Connects to backend monitoring when server is running
              </p>
            </div>
          </GlassCard>
        </motion.div>
      )}
    </div>
  );
}
