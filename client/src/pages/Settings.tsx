/**
 * VisionX — Settings Page (MODE 3: Configuration)
 * Module toggles, rule builder, device manager, performance mode
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlassCard } from '../components/ui/GlassCard';
import { useThemeStore, THEMES } from '../stores/themeStore';

interface ModuleToggle {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  icon: string;
  tier: 'free' | 'pro' | 'enterprise';
}

const initialModules: ModuleToggle[] = [
  { id: 'detection', name: 'Object Detection', description: 'YOLO-based object detection', enabled: true, icon: '🎯', tier: 'free' },
  { id: 'tracking', name: 'Object Tracking', description: 'Multi-object tracker with persistent IDs', enabled: true, icon: '⟐', tier: 'pro' },
  { id: 'counting', name: 'Object Counting', description: 'Count objects per class in real-time', enabled: true, icon: '🔢', tier: 'free' },
  { id: 'ocr', name: 'Text Recognition', description: 'Read text, license plates, signs', enabled: false, icon: '📝', tier: 'pro' },
  { id: 'face', name: 'Face Recognition', description: 'Identify known faces from database', enabled: false, icon: '👤', tier: 'enterprise' },
  { id: 'pose', name: 'Pose Estimation', description: 'Human skeleton detection', enabled: false, icon: '🏃', tier: 'enterprise' },
  { id: 'segmentation', name: 'Segmentation', description: 'Pixel-level object segmentation', enabled: false, icon: '🗺️', tier: 'enterprise' },
];

const performanceModes = [
  { id: 'lite', name: 'Lite', desc: '320px • INT8 • 15 FPS', icon: '🔋', detail: 'Mobile / Raspberry Pi' },
  { id: 'balanced', name: 'Balanced', desc: '640px • FP16 • 30 FPS', icon: '⚖️', detail: 'Laptop / Desktop' },
  { id: 'max', name: 'Maximum', desc: '1280px • FP32 • 60 FPS', icon: '🚀', detail: 'GPU Server / Jetson' },
];

export default function Settings() {
  const [modules, setModules] = useState(initialModules);
  const [perfMode, setPerfMode] = useState('balanced');
  const [confThreshold, setConfThreshold] = useState(50);
  const { theme, setTheme } = useThemeStore();

  const toggleModule = (id: string) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, enabled: !m.enabled } : m));
  };

  return (
    <div className="settings">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* AI Modules */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>AI Modules</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {modules.map((mod) => (
                <div key={mod.id} className="glass-subtle" style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '14px 16px', borderRadius: 'var(--radius-sm)',
                  opacity: mod.enabled ? 1 : 0.6,
                  transition: 'opacity var(--transition-fast)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ fontSize: 20 }}>{mod.icon}</span>
                    <div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span className="font-medium text-sm">{mod.name}</span>
                        <span className={`badge badge-${mod.tier === 'free' ? 'success' : mod.tier === 'pro' ? 'accent' : 'warning'}`}
                          style={{ fontSize: '0.6rem', padding: '2px 6px' }}>
                          {mod.tier.toUpperCase()}
                        </span>
                      </div>
                      <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{mod.description}</span>
                    </div>
                  </div>
                  <label style={{ position: 'relative', width: 44, height: 24, cursor: 'pointer' }}>
                    <input type="checkbox" checked={mod.enabled} onChange={() => toggleModule(mod.id)}
                      style={{ opacity: 0, width: 0, height: 0 }} />
                    <span style={{
                      position: 'absolute', inset: 0, borderRadius: 12,
                      background: mod.enabled ? 'var(--accent)' : 'var(--surface)',
                      border: '1px solid var(--border)',
                      transition: 'background var(--transition-fast)',
                    }}>
                      <span style={{
                        position: 'absolute', top: 3, left: mod.enabled ? 22 : 3,
                        width: 16, height: 16, borderRadius: '50%', background: '#fff',
                        transition: 'left var(--transition-fast)',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                      }} />
                    </span>
                  </label>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Performance Mode */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Performance Mode</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {performanceModes.map((pm) => (
                  <motion.div
                    key={pm.id}
                    className={`glass-subtle ${perfMode === pm.id ? 'glow-border' : ''}`}
                    style={{
                      padding: '14px 16px', borderRadius: 'var(--radius-sm)', cursor: 'pointer',
                      border: perfMode === pm.id ? '1px solid var(--accent)' : '1px solid var(--border)',
                    }}
                    onClick={() => setPerfMode(pm.id)}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontSize: 18, marginRight: 10 }}>{pm.icon}</span>
                        <span className="font-semibold">{pm.name}</span>
                      </div>
                      {perfMode === pm.id && <span className="badge badge-accent">Active</span>}
                    </div>
                    <p className="text-xs mono" style={{ color: 'var(--text-secondary)', marginTop: 4, marginLeft: 32 }}>{pm.desc}</p>
                    <p className="text-xs" style={{ color: 'var(--text-tertiary)', marginLeft: 32 }}>{pm.detail}</p>
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>

          {/* Detection Settings */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Detection Settings</h3>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="text-sm">Confidence Threshold</span>
                  <span className="mono text-sm font-bold" style={{ color: 'var(--accent)' }}>{confThreshold}%</span>
                </div>
                <input type="range" min={10} max={95} value={confThreshold} onChange={(e) => setConfThreshold(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--accent)' }} />
              </div>
            </GlassCard>
          </motion.div>

          {/* Theme Selector */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <GlassCard>
              <h3 className="font-semibold" style={{ marginBottom: 16 }}>Visual Theme</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                {THEMES.map((t) => (
                  <motion.button
                    key={t.id}
                    onClick={() => setTheme(t.id)}
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.95 }}
                    style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                      padding: '12px 8px', borderRadius: 'var(--radius-md)', cursor: 'pointer',
                      background: theme === t.id ? 'var(--accent-subtle)' : 'var(--surface)',
                      border: theme === t.id ? '2px solid var(--accent)' : '1px solid var(--border)',
                    }}
                  >
                    <span style={{
                      width: 24, height: 24, borderRadius: '50%', background: t.accent,
                      boxShadow: theme === t.id ? `0 0 12px ${t.accent}` : 'none',
                    }} />
                    <span className="text-xs font-medium">{t.name}</span>
                  </motion.button>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
