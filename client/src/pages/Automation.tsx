/**
 * VisionX — Automation Page (MODE 4: Jarvis Mode)
 * "If this → do that" automation builder with visual rule cards
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { GlowButton } from '../components/ui/GlowButton';

interface AutoRule {
  id: number;
  name: string;
  trigger: string;
  actions: string[];
  enabled: boolean;
  lastTriggered?: string;
  triggerCount: number;
}

const initialRules: AutoRule[] = [
  {
    id: 1, name: 'Crowd Alert',
    trigger: 'Person count > 10 in Zone A',
    actions: ['Send email alert', 'Push notification', 'Sound alarm'],
    enabled: true, lastTriggered: '5 min ago', triggerCount: 23,
  },
  {
    id: 2, name: 'Intrusion Detection',
    trigger: 'Person detected in Restricted Zone',
    actions: ['Capture screenshot', 'Send webhook', 'Notify admin'],
    enabled: true, lastTriggered: '1 hour ago', triggerCount: 7,
  },
  {
    id: 3, name: 'Vehicle Monitoring',
    trigger: 'Unknown vehicle parked > 10 min',
    actions: ['Log event', 'Send email to security'],
    enabled: false, lastTriggered: 'Never', triggerCount: 0,
  },
  {
    id: 4, name: 'Safety Check',
    trigger: 'No helmet detected on person',
    actions: ['Flash warning on screen', 'Log violation'],
    enabled: true, lastTriggered: '30 min ago', triggerCount: 45,
  },
];

const triggerTemplates = [
  'Person count > N in [zone]',
  'Person detected in [restricted zone]',
  'Vehicle detected in [zone]',
  'No helmet/vest on person',
  'Object left unattended > N min',
  'Camera offline > N min',
  'Face [known/unknown] detected',
];

const actionTemplates = [
  '📧 Send email alert',
  '🔔 Push notification',
  '📸 Capture screenshot',
  '🔗 Send webhook',
  '🔊 Sound alarm',
  '💾 Log event',
  '📱 SMS alert',
  '🤖 API call',
];

const executionLog = [
  { id: 1, rule: 'Crowd Alert', time: '14:32:05', status: 'success', actions: 3 },
  { id: 2, rule: 'Safety Check', time: '14:28:11', status: 'success', actions: 2 },
  { id: 3, rule: 'Intrusion Detection', time: '13:15:44', status: 'failed', actions: 0 },
  { id: 4, rule: 'Crowd Alert', time: '13:02:22', status: 'success', actions: 3 },
];

export default function Automation() {
  const [rules, setRules] = useState(initialRules);
  const [showBuilder, setShowBuilder] = useState(false);

  const toggleRule = (id: number) => {
    setRules(prev => prev.map(r => r.id === id ? { ...r, enabled: !r.enabled } : r));
  };

  return (
    <div className="automation">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h2 className="text-2xl font-bold" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ color: 'var(--accent)' }}>⚡</span> Jarvis Mode
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
            Detect → Decide → Act — automatically
          </p>
        </div>
        <GlowButton onClick={() => setShowBuilder(!showBuilder)}>
          {showBuilder ? '✕ Close' : '+ New Rule'}
        </GlowButton>
      </div>

      {/* Rule Builder (toggleable) */}
      <AnimatePresence>
        {showBuilder && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            style={{ marginBottom: 20, overflow: 'hidden' }}
          >
            <GlassCard className="glow-border">
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Create New Rule</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                {/* Triggers */}
                <div>
                  <p className="text-sm font-medium" style={{ marginBottom: 8, color: 'var(--text-secondary)' }}>
                    IF (Trigger)
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {triggerTemplates.map((t, i) => (
                      <motion.div
                        key={i}
                        className="glass-subtle"
                        style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
                        whileHover={{ scale: 1.01, borderColor: 'var(--accent)' }}
                      >
                        <span className="text-sm">{t}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div>
                  <p className="text-sm font-medium" style={{ marginBottom: 8, color: 'var(--text-secondary)' }}>
                    THEN (Actions)
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {actionTemplates.map((a, i) => (
                      <motion.div
                        key={i}
                        className="glass-subtle"
                        style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}
                        whileHover={{ scale: 1.01, borderColor: 'var(--accent)' }}
                      >
                        <span className="text-sm">{a}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
                <GlowButton>Save Rule</GlowButton>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20 }}>
        {/* Active Rules */}
        <div>
          <h3 className="font-semibold" style={{ marginBottom: 12 }}>Active Rules ({rules.filter(r => r.enabled).length})</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {rules.map((rule, i) => (
              <motion.div
                key={rule.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <GlassCard style={{ opacity: rule.enabled ? 1 : 0.5, transition: 'opacity 0.3s' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                        <span className="font-semibold">{rule.name}</span>
                        <span className={`badge ${rule.enabled ? 'badge-success' : 'badge-danger'}`}>
                          {rule.enabled ? 'ON' : 'OFF'}
                        </span>
                      </div>
                      <p className="text-sm" style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>
                        <strong>IF:</strong> {rule.trigger}
                      </p>
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {rule.actions.map((a, j) => (
                          <span key={j} className="badge badge-accent">{a}</span>
                        ))}
                      </div>
                      <div className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 8 }}>
                        Last: {rule.lastTriggered} · Triggered {rule.triggerCount}x
                      </div>
                    </div>
                    <label style={{ position: 'relative', width: 44, height: 24, cursor: 'pointer', flexShrink: 0 }}>
                      <input type="checkbox" checked={rule.enabled} onChange={() => toggleRule(rule.id)}
                        style={{ opacity: 0, width: 0, height: 0 }} />
                      <span style={{
                        position: 'absolute', inset: 0, borderRadius: 12,
                        background: rule.enabled ? 'var(--accent)' : 'var(--surface)',
                        border: '1px solid var(--border)', transition: 'background var(--transition-fast)',
                      }}>
                        <span style={{
                          position: 'absolute', top: 3, left: rule.enabled ? 22 : 3,
                          width: 16, height: 16, borderRadius: '50%', background: '#fff',
                          transition: 'left var(--transition-fast)', boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                        }} />
                      </span>
                    </label>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Execution Log */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 12 }}>Execution Log</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {executionLog.map((log) => (
                <div key={log.id} className="glass-subtle" style={{
                  padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                  borderLeft: `3px solid ${log.status === 'success' ? 'var(--success)' : 'var(--danger)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="text-sm font-medium">{log.rule}</span>
                    <span className={`badge ${log.status === 'success' ? 'badge-success' : 'badge-danger'}`}>
                      {log.status}
                    </span>
                  </div>
                  <div className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
                    {log.time} · {log.actions} actions executed
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
