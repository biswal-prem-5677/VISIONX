/**
 * VisionX — User Home Page
 * Personal dashboard: my devices, my events, usage, account
 */

import { motion } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

const userProfile = {
  name: 'Prem Biswal',
  email: 'prem@visionx.ai',
  plan: 'Pro',
  joined: 'Mar 2026',
  avatar: 'P',
};

const myDevices = [
  { id: 1, name: 'Camera_01', location: 'Main Entrance', status: 'online', fps: 30, uptime: '99.2%' },
  { id: 2, name: 'Camera_02', location: 'Parking Lot', status: 'online', fps: 25, uptime: '98.7%' },
  { id: 3, name: 'Camera_03', location: 'Warehouse', status: 'offline', fps: 0, uptime: '45.3%' },
];

const recentActivity = [
  { id: 1, action: 'Rule triggered: Crowd Alert', time: '10 min ago', type: 'warning' },
  { id: 2, action: 'Camera_02 reconnected', time: '1 hour ago', type: 'success' },
  { id: 3, action: 'Settings updated: Performance → Max', time: '3 hours ago', type: 'info' },
  { id: 4, action: 'Rule created: Night Watch', time: '1 day ago', type: 'info' },
];

const usageStats = [
  { label: 'Detections This Month', value: '12,847' },
  { label: 'Events Triggered', value: '342' },
  { label: 'API Calls', value: '8,921' },
  { label: 'Storage Used', value: '2.3 GB' },
];

export default function UserHome() {
  return (
    <div className="user-home">
      {/* Profile Header */}
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <GlassCard style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--accent), var(--accent-hover))',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.4rem', fontWeight: 800, color: '#fff',
              }}>
                {userProfile.avatar}
              </div>
              <div>
                <h2 className="text-xl font-bold">{userProfile.name}</h2>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{userProfile.email}</p>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className="badge badge-accent">{userProfile.plan} Plan</span>
              <GlowButton variant="ghost" size="sm">Edit Profile</GlowButton>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Usage Stats */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        {usageStats.map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}>
            <GlassCard className="stat-card">
              <div className="stat-card__info">
                <span className="stat-card__value">{stat.value}</span>
                <span className="stat-card__label">{stat.label}</span>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* My Devices */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <GlassCard>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <h3 className="font-semibold">My Devices</h3>
              <GlowButton size="sm">+ Add Camera</GlowButton>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {myDevices.map((device) => (
                <div key={device.id} className="glass-subtle" style={{
                  padding: '14px 16px', borderRadius: 'var(--radius-sm)',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      width: 8, height: 8, borderRadius: '50%',
                      background: device.status === 'online' ? 'var(--success)' : 'var(--danger)',
                    }} />
                    <div>
                      <span className="font-medium text-sm">{device.name}</span>
                      <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>
                        {device.location}
                      </span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <span className="text-xs mono">{device.fps} FPS</span>
                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                      {device.uptime} uptime
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>

        {/* Recent Activity */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Recent Activity</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentActivity.map((activity) => (
                <div key={activity.id} className="glass-subtle" style={{
                  padding: '12px 16px', borderRadius: 'var(--radius-sm)',
                  borderLeft: `3px solid var(--${activity.type === 'warning' ? 'warning' : activity.type === 'success' ? 'success' : 'info'})`,
                }}>
                  <span className="text-sm">{activity.action}</span>
                  <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block', marginTop: 4 }}>
                    {activity.time}
                  </span>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
