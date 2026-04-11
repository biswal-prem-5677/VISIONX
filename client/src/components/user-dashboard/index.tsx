/**
 * VisionX — User Dashboard sub-components
 * UserOverview, MyDevices, MyEvents, UsageStats, AccountSettings, BillingPanel
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

// ─── UserOverview ──────────────────────────────────

interface UserProfile {
  name: string; email: string; plan: string; avatar: string; joined: string;
}

export function UserOverview({ user, onEdit }: { user: UserProfile; onEdit?: () => void }) {
  return (
    <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{
          width: 56, height: 56, borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--accent), var(--accent-hover))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.4rem', fontWeight: 800, color: '#fff',
        }}>
          {user.avatar}
        </div>
        <div>
          <h2 className="text-xl font-bold">{user.name}</h2>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{user.email}</p>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span className="badge badge-accent">{user.plan}</span>
        <GlowButton variant="ghost" size="sm" onClick={onEdit}>Edit Profile</GlowButton>
      </div>
    </div>
  );
}

// ─── MyDevices ──────────────────────────────────

interface Device {
  id: number; name: string; location: string; status: 'online' | 'offline'; fps: number; uptime: string;
}

export function MyDevices({ devices, onAdd }: { devices: Device[]; onAdd?: () => void }) {
  return (
    <div className="glass-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 className="font-semibold">My Devices</h3>
        <GlowButton size="sm" onClick={onAdd}>+ Add Camera</GlowButton>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {devices.map((d) => (
          <div key={d.id} className="glass-subtle" style={{
            padding: '12px 14px', borderRadius: 'var(--radius-sm)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: d.status === 'online' ? 'var(--success)' : 'var(--danger)',
              }} />
              <div>
                <span className="font-medium text-sm">{d.name}</span>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>{d.location}</span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span className="text-xs mono">{d.fps} FPS</span>
              <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{d.uptime}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── MyEvents ──────────────────────────────────

interface UserEvent {
  id: number; action: string; time: string; type: 'info' | 'warning' | 'success';
}

export function MyEvents({ events }: { events: UserEvent[] }) {
  return (
    <div className="glass-card">
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Recent Activity</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {events.map((e) => (
          <div key={e.id} className="glass-subtle" style={{
            padding: '10px 14px', borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid var(--${e.type})`,
          }}>
            <span className="text-sm">{e.action}</span>
            <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block', marginTop: 2 }}>{e.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── UsageStats ──────────────────────────────────

export function UsageStats({ stats }: { stats: { label: string; value: string }[] }) {
  return (
    <div className="grid grid-4">
      {stats.map((s, i) => (
        <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08 }} className="glass-card stat-card">
          <div className="stat-card__info">
            <span className="stat-card__value">{s.value}</span>
            <span className="stat-card__label">{s.label}</span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ─── AccountSettings ──────────────────────────────────

export function AccountSettings() {
  const [name, setName] = useState('Prem Biswal');
  const [email, setEmail] = useState('prem@visionx.ai');

  return (
    <div className="glass-card">
      <h3 className="font-semibold" style={{ marginBottom: 16 }}>Account Settings</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} style={{
            width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none', fontFamily: 'var(--font-sans)',
          }} />
        </div>
        <div>
          <label className="text-xs font-medium" style={{ color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{
            width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none', fontFamily: 'var(--font-sans)',
          }} />
        </div>
        <GlowButton size="sm">Save Changes</GlowButton>
      </div>
    </div>
  );
}

// ─── BillingPanel ──────────────────────────────────

export function BillingPanel({ plan, nextBilling }: { plan: string; nextBilling: string }) {
  return (
    <div className="glass-card">
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Billing & Subscription</h3>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <span className="badge badge-accent" style={{ marginRight: 8 }}>{plan} Plan</span>
          <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Next billing: {nextBilling}</span>
        </div>
        <GlowButton variant="secondary" size="sm">Manage</GlowButton>
      </div>
      <div style={{ display: 'flex', gap: 12 }}>
        <GlowButton variant="ghost" size="sm">View Invoices</GlowButton>
        <GlowButton variant="ghost" size="sm">Update Payment</GlowButton>
      </div>
    </div>
  );
}
