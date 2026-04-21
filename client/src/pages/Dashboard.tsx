/**
 * VisionX — Dashboard Page (MODE 1: Live Monitoring)
 * Real-time camera feed, detections, alerts, status
 * Wired to visionStore + eventStore via WebSocket
 */

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';
import { useVisionStore } from '../stores/visionStore';
import { useEventStore } from '../stores/eventStore';

export default function Dashboard() {
  const { detections, fps, latency, isProcessing, frameCount } = useVisionStore();
  const { events, activeAlerts, acknowledgeEvent } = useEventStore();

  // Derive live stats from stores (reactive)
  const statCards = [
    { label: 'Live Objects', value: String(detections.length), icon: '◉', color: 'var(--success)' },
    { label: 'Active Tracks', value: String(new Set(detections.filter(d => d.trackId).map(d => d.trackId)).size), icon: '⟐', color: 'var(--accent)' },
    { label: 'Events Today', value: String(events.length), icon: '⚡', color: 'var(--warning)' },
    { label: 'Active Alerts', value: String(activeAlerts), icon: '◈', color: activeAlerts > 0 ? 'var(--danger)' : 'var(--info)' },
  ];

  // Recent 4 alerts
  const recentAlerts = events.slice(0, 4);

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
                  background: isProcessing ? 'var(--success)' : 'var(--danger)',
                  boxShadow: isProcessing ? '0 0 12px var(--success)' : 'none',
                  animation: isProcessing ? 'pulse-glow 2s infinite' : 'none',
                }} />
                <span className="font-semibold">Camera_01 — Main Entrance</span>
              </div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="badge badge-success mono" style={{ fontSize: '0.7rem' }}>
                  {fps > 0 ? `${fps.toFixed(0)} FPS` : '— FPS'}
                </span>
                <span className="badge badge-info mono" style={{ fontSize: '0.7rem' }}>
                  {latency > 0 ? `${latency.toFixed(0)}ms` : '—ms'}
                </span>
                <span className="badge mono" style={{ fontSize: '0.7rem', background: 'var(--bg-tertiary)' }}>
                  F#{frameCount}
                </span>
              </div>
            </div>

            {/* Feed Area */}
            <div style={{
              height: 420, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(135deg, var(--bg-secondary), var(--bg-tertiary))',
              position: 'relative',
            }}>
              {detections.length === 0 ? (
                <div style={{ textAlign: 'center', opacity: 0.5 }}>
                  <div style={{ fontSize: 48, marginBottom: 12 }}>📹</div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    Waiting for detections...
                  </p>
                  <p className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
                    WebSocket → Pipeline → BoundingBox overlay
                  </p>
                </div>
              ) : (
                /* Render detection boxes dynamically */
                detections.slice(0, 8).map((d, i) => (
                  <div
                    key={d.id}
                    style={{
                      position: 'absolute',
                      top: 40 + (i * 40) % 300,
                      left: 60 + (i * 120) % 500,
                      width: 100 + (i % 3) * 30,
                      height: 80 + (i % 2) * 60,
                      border: `2px solid ${d.class === 'person' ? 'var(--success)' : 'var(--accent)'}`,
                      borderRadius: 4,
                    }}
                  >
                    <span style={{
                      position: 'absolute', top: -20, left: 0,
                      background: d.class === 'person' ? 'var(--success)' : 'var(--accent)',
                      color: '#000', fontSize: 10,
                      padding: '2px 6px', borderRadius: 4, fontWeight: 600,
                    }}>
                      {d.trackId ? `ID:${d.trackId} | ` : ''}{d.class} {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))
              )}
            </div>

            {/* Feed Footer */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '12px 20px', borderTop: '1px solid var(--border)',
            }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                  {detections.length} objects detected
                </span>
              </div>
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
                {detections.length === 0 ? (
                  <p className="text-sm" style={{ opacity: 0.5, textAlign: 'center', padding: 20 }}>
                    No detections yet
                  </p>
                ) : (
                  detections.slice(0, 8).map((d) => (
                    <div key={d.id} className="glass-subtle" style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                    }}>
                      <div>
                        <span className="font-medium">{d.class}</span>
                        {d.trackId && (
                          <span className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginLeft: 8 }}>
                            ID:{d.trackId}
                          </span>
                        )}
                      </div>
                      <span className="badge badge-accent">{(d.confidence * 100).toFixed(0)}%</span>
                    </div>
                  ))
                )}
              </div>
            </GlassCard>
          </motion.div>

          {/* Alerts — from eventStore */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <GlassCard>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 className="font-semibold">Recent Alerts</h3>
                {activeAlerts > 0 && (
                  <span className="badge badge-danger">{activeAlerts} active</span>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {recentAlerts.length === 0 ? (
                  <p className="text-sm" style={{ opacity: 0.5, textAlign: 'center', padding: 20 }}>
                    No alerts
                  </p>
                ) : (
                  recentAlerts.map((a) => (
                    <div
                      key={a.id}
                      className="glass-subtle"
                      style={{
                        padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                        borderLeft: `3px solid var(--${a.severity === 'danger' ? 'danger' : a.severity === 'warning' ? 'warning' : 'info'})`,
                        opacity: a.acknowledged ? 0.5 : 1,
                        cursor: a.acknowledged ? 'default' : 'pointer',
                      }}
                      onClick={() => !a.acknowledged && acknowledgeEvent(a.id)}
                    >
                      <p className="text-sm font-medium">{a.message}</p>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                          {a.camera}
                        </span>
                        <span className="text-xs mono" style={{ color: 'var(--text-tertiary)' }}>
                          {new Date(a.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
