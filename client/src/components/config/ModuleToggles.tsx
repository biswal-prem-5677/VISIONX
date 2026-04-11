/**
 * VisionX — ModuleToggles Component
 * Enable/disable AI modules with tier badges
 */

import { useState } from 'react';
import { motion } from 'framer-motion';

interface AIModule {
  id: string;
  name: string;
  description: string;
  tier: 'FREE' | 'PRO' | 'ENTERPRISE';
  enabled: boolean;
}

interface ModuleTogglesProps {
  modules: AIModule[];
  onChange?: (id: string, enabled: boolean) => void;
}

const TIER_COLORS = { FREE: '#22c55e', PRO: '#a78bfa', ENTERPRISE: '#fbbf24' };

export function ModuleToggles({ modules, onChange }: ModuleTogglesProps) {
  const [state, setState] = useState(modules);

  const toggle = (id: string) => {
    setState((s) =>
      s.map((m) => m.id === id ? { ...m, enabled: !m.enabled } : m)
    );
    const mod = state.find((m) => m.id === id);
    if (mod) onChange?.(id, !mod.enabled);
  };

  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>AI Modules</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {state.map((mod) => (
          <div key={mod.id} className="glass-subtle" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '14px 16px', borderRadius: 'var(--radius-sm)',
            opacity: mod.enabled ? 1 : 0.6,
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="font-medium text-sm">{mod.name}</span>
                <span className="text-xs" style={{
                  padding: '2px 6px', borderRadius: 4, fontWeight: 700,
                  color: TIER_COLORS[mod.tier], background: `${TIER_COLORS[mod.tier]}15`,
                  fontSize: '0.55rem',
                }}>
                  {mod.tier}
                </span>
              </div>
              <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{mod.description}</span>
            </div>
            <motion.button
              onClick={() => toggle(mod.id)}
              whileTap={{ scale: 0.9 }}
              style={{
                width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                background: mod.enabled ? 'var(--accent)' : 'var(--surface)',
                position: 'relative', transition: 'background 0.3s',
              }}
            >
              <motion.div
                style={{
                  width: 18, height: 18, borderRadius: '50%', background: '#fff',
                  position: 'absolute', top: 3,
                }}
                animate={{ left: mod.enabled ? 23 : 3 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              />
            </motion.button>
          </div>
        ))}
      </div>
    </div>
  );
}
