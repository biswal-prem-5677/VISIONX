/**
 * VisionX — Admin sub-components
 * AdminOverview, UserTable, UserTakeover, SystemHealth,
 * CrashReports, FeatureUsageMap, RemoteConfig, AbuseLog
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

// ─── AdminOverview ──────────────────────────────────

interface SystemStat {
  label: string; value: string; change: string; icon: string; color: string;
}

export function AdminOverview({ stats }: { stats: SystemStat[] }) {
  return (
    <div className="grid grid-4">
      {stats.map((s, i) => (
        <motion.div key={s.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08 }} className="glass-card stat-card">
          <div className="stat-card__icon" style={{ color: s.color }}>{s.icon}</div>
          <div className="stat-card__info">
            <span className="stat-card__value">{s.value}</span>
            <span className="stat-card__label">{s.label}</span>
          </div>
          <span className="badge badge-success" style={{ marginLeft: 'auto', fontSize: '0.6rem' }}>{s.change}</span>
        </motion.div>
      ))}
    </div>
  );
}

// ─── UserTable ──────────────────────────────────

interface User {
  id: number; name: string; email: string; plan: string; status: string;
  cameras: number; lastActive: string;
}

export function UserTable({ users, onView }: { users: User[]; onView?: (id: number) => void }) {
  const [search, setSearch] = useState('');
  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
        <h3 className="font-semibold">Users ({filtered.length})</h3>
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Search users..."
          style={{
            padding: '6px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none',
            fontFamily: 'var(--font-sans)',
          }}
        />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {filtered.map((u) => (
          <div key={u.id} className="glass-subtle" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '12px 16px', borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%', background: 'var(--accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '0.75rem', fontWeight: 700, color: '#fff',
              }}>{u.name[0]}</div>
              <div>
                <span className="font-medium text-sm">{u.name}</span>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>{u.email}</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="badge badge-accent" style={{ fontSize: '0.55rem' }}>{u.plan}</span>
              <span className="text-xs mono">{u.cameras} cam</span>
              <GlowButton variant="ghost" size="sm" onClick={() => onView?.(u.id)}>View</GlowButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── UserTakeover ──────────────────────────────────

export function UserTakeover({ onTakeover }: { onTakeover?: (userId: number) => void }) {
  const [userId, setUserId] = useState('');
  return (
    <div className="glass-card" style={{ padding: 20 }}>
      <h3 className="font-semibold" style={{ marginBottom: 8 }}>🎭 User Takeover</h3>
      <p className="text-xs" style={{ color: 'var(--text-secondary)', marginBottom: 12 }}>
        Impersonate a user session for debugging. All actions are audit-logged.
      </p>
      <div style={{ display: 'flex', gap: 8 }}>
        <input value={userId} onChange={(e) => setUserId(e.target.value)}
          placeholder="User ID" style={{
            flex: 1, padding: '8px 12px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface)', border: '1px solid var(--border)',
            color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none',
            fontFamily: 'var(--font-sans)',
          }}
        />
        <GlowButton variant="danger" size="sm" onClick={() => onTakeover?.(parseInt(userId))}>
          Impersonate
        </GlowButton>
      </div>
    </div>
  );
}

// ─── SystemHealth ──────────────────────────────────

interface HealthMetric {
  name: string; value: number; max: number; unit: string;
}

export function SystemHealth({ metrics }: { metrics: HealthMetric[] }) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>💚 System Health</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {metrics.map((m) => {
          const pct = (m.value / m.max) * 100;
          const color = pct > 80 ? 'var(--danger)' : pct > 60 ? 'var(--warning)' : 'var(--success)';
          return (
            <div key={m.name}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span className="text-sm">{m.name}</span>
                <span className="text-sm mono" style={{ color }}>{m.value}{m.unit} / {m.max}{m.unit}</span>
              </div>
              <div style={{ height: 6, borderRadius: 3, background: 'var(--surface)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.5s' }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── CrashReports ──────────────────────────────────

interface CrashReport {
  id: number; error: string; count: number; users: number; severity: string; lastSeen: string;
}

export function CrashReports({ reports }: { reports: CrashReport[] }) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>💥 Crash Reports</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {reports.map((r) => (
          <div key={r.id} className="glass-subtle" style={{
            padding: '12px 16px', borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid ${r.severity === 'high' ? 'var(--danger)' : r.severity === 'medium' ? 'var(--warning)' : 'var(--info)'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span className="font-medium text-sm">{r.error}</span>
              <span className={`badge badge-${r.severity === 'high' ? 'danger' : 'warning'}`}>{r.severity}</span>
            </div>
            <div className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
              {r.count} occurrences · {r.users} users · {r.lastSeen}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── FeatureUsageMap ──────────────────────────────────

export function FeatureUsageMap({ features }: { features: { name: string; usage: number; max: number }[] }) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>📊 Feature Usage</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {features.map((f) => (
          <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="text-sm" style={{ minWidth: 120 }}>{f.name}</span>
            <div style={{ flex: 1, height: 8, borderRadius: 4, background: 'var(--surface)', overflow: 'hidden' }}>
              <div style={{
                height: '100%', width: `${(f.usage / f.max) * 100}%`,
                background: 'var(--accent)', borderRadius: 4,
              }} />
            </div>
            <span className="text-xs mono" style={{ minWidth: 50, textAlign: 'right' }}>{f.usage}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── RemoteConfig ──────────────────────────────────

export function RemoteConfig({ configs, onUpdate }: {
  configs: { key: string; value: string; description: string }[];
  onUpdate?: (key: string, value: string) => void;
}) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>⚙️ Remote Config</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {configs.map((c) => (
          <div key={c.key} className="glass-subtle" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '12px 14px', borderRadius: 'var(--radius-sm)',
          }}>
            <div>
              <span className="font-medium text-sm mono">{c.key}</span>
              <span className="text-xs" style={{ color: 'var(--text-tertiary)', display: 'block' }}>{c.description}</span>
            </div>
            <input value={c.value} onChange={(e) => onUpdate?.(c.key, e.target.value)}
              style={{
                width: 100, padding: '4px 8px', borderRadius: 4,
                background: 'var(--surface)', border: '1px solid var(--border)',
                color: 'var(--text-primary)', fontSize: '0.8rem', textAlign: 'right',
                outline: 'none', fontFamily: 'var(--font-mono)',
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── AbuseLog ──────────────────────────────────

export function AbuseLog({ entries }: {
  entries: { id: number; userId: string; action: string; severity: string; time: string }[];
}) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>🚨 Abuse Log</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {entries.length === 0 ? (
          <p className="text-sm" style={{ padding: 20, textAlign: 'center', color: 'var(--text-tertiary)' }}>
            No suspicious activity detected
          </p>
        ) : (
          entries.map((e) => (
            <div key={e.id} className="glass-subtle" style={{
              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
              borderLeft: `3px solid ${e.severity === 'critical' ? 'var(--danger)' : 'var(--warning)'}`,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span className="text-sm">{e.action}</span>
                <span className="text-xs mono" style={{ color: 'var(--text-tertiary)' }}>{e.time}</span>
              </div>
              <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>User: {e.userId}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
