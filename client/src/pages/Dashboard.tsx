/**
 * VisionX — Dashboard Page (MODE 1: Live Monitoring)
 * Real-time camera feed, detections, alerts, status
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

const mockDetections = [
  { id: 1, label: 'Person', confidence: 0.94, trackId: 12 },
  { id: 2, label: 'Car', confidence: 0.87, trackId: 5 },
  { id: 3, label: 'Person', confidence: 0.91, trackId: 14 },
  { id: 4, label: 'Bicycle', confidence: 0.78, trackId: 8 },
];

const mockAlerts = [
  { id: 1, type: 'warning', message: 'Crowd threshold exceeded (>5 persons)', time: '2 min ago' },
  { id: 2, type: 'danger', message: 'Restricted zone intrusion detected', time: '5 min ago' },
  { id: 3, type: 'info', message: 'New device connected: Camera_02', time: '12 min ago' },
];

const statCards = [
  { label: 'Live Objects', value: '12', icon: '◉', color: 'var(--success)' },
  { label: 'Active Tracks', value: '8', icon: '⟐', color: 'var(--accent)' },
  { label: 'Events Today', value: '47', icon: '⚡', color: 'var(--warning)' },
  { label: 'Cameras Online', value: '3/4', icon: '◈', color: 'var(--info)' },
];

export default function Dashboard() {
  const [isLive, setIsLive] = useState(true);

  return (
    <div className="dashboard">
      {/* Stats Row */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        {statCards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <GlassCard className="stat-card">
              <div className="stat-card__icon" style={{ color: card.color }}>{card.icon}</div>
              <div className="stat-card__info">
                <span className="stat-card__value">{card.value}</span>
                <span className="stat-card__label">{card.label}</span>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Main Grid: Feed + Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20 }}>
        {/* Live Feed */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
            {/* Feed Header */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '16px 20px', borderBottom: '1px solid var(--border)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: isLive ? 'var(--success)' : 'var(--danger)',
                  boxShadow: isLive ? '0 0 12px var(--success)' : 'none',
                  animation: isLive ? 'pulse-glow 2s infinite' : 'none',
                }} />
                <span className="font-semibold">Camera_01 — Main Entrance</span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="badge badge-success mono" style={{ fontSize: '0.7rem' }}>
                  30 FPS
                </span>
                <span className="badge badge-info mono" style={{ fontSize: '0.7rem' }}>
                  12ms
                </span>
              </div>
            </div>

            {/* Feed Placeholder */}
            <div style={{
              height: 420, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary))',
              position: 'relative',
            }}>
              <div style={{ textAlign: 'center', opacity: 0.5 }}>
                <div style={{ fontSize: 48, marginBottom: 12 }}>📹</div>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  Live camera feed will render here
                </p>
                <p className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
                  WebSocket → Canvas → BoundingBox overlay
                </p>
              </div>

              {/* Mock detection boxes */}
              <div style={{
                position: 'absolute', top: 60, left: 80,
                width: 100, height: 160, border: '2px solid var(--success)',
                borderRadius: 4,
              }}>
                <span style={{
                  position: 'absolute', top: -20, left: 0,
                  background: 'var(--success)', color: '#000', fontSize: 10,
                  padding: '2px 6px', borderRadius: 4, fontWeight: 600,
                }}>ID:12 | Person 94%</span>
              </div>
              <div style={{
                position: 'absolute', top: 120, right: 120,
                width: 140, height: 80, border: '2px solid #00e5ff',
                borderRadius: 4,
              }}>
                <span style={{
                  position: 'absolute', top: -20, left: 0,
                  background: '#00e5ff', color: '#000', fontSize: 10,
                  padding: '2px 6px', borderRadius: 4, fontWeight: 600,
                }}>ID:5 | Car 87%</span>
              </div>
            </div>

            {/* Feed Footer */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 20px', borderTop: '1px solid var(--border)',
            }}>
              <GlowButton size="sm" onClick={() => setIsLive(!isLive)}>
                {isLive ? '⏸ Pause' : '▶ Resume'}
              </GlowButton>
              <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                Resolution: 1280×720 | Mode: Balanced
              </span>
            </div>
          </GlassCard>
        </motion.div>

        {/* Right Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Active Detections */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 12 }}>Active Detections</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {mockDetections.map((d) => (
                  <div key={d.id} className="glass-subtle" style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                  }}>
                    <div>
                      <span className="font-medium">{d.label}</span>
                      <span className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginLeft: 8 }}>
                        ID:{d.trackId}
                      </span>
                    </div>
                    <span className="badge badge-accent">{(d.confidence * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>

          {/* Alerts */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 12 }}>Recent Alerts</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {mockAlerts.map((a) => (
                  <div key={a.id} className="glass-subtle" style={{
                    padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                    borderLeft: `3px solid var(--${a.type === 'danger' ? 'danger' : a.type === 'warning' ? 'warning' : 'info'})`,
                  }}>
                    <p className="text-sm font-medium">{a.message}</p>
                    <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>{a.time}</p>
                  </div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
