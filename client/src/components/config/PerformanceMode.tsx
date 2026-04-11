/**
 * VisionX — PerformanceMode Component
 * Lite / Balanced / Max mode selector
 */

import { useState } from 'react';
import { motion } from 'framer-motion';

interface PerformanceModeProps {
  defaultMode?: string;
  onChange?: (mode: string) => void;
}

const MODES = [
  { id: 'lite', label: '⚡ Lite', desc: '320p · 15 FPS · CPU only', color: '#22c55e' },
  { id: 'balanced', label: '⚖️ Balanced', desc: '640p · 30 FPS · GPU-assisted', color: '#38bdf8' },
  { id: 'max', label: '🔥 Max', desc: '1280p · 60 FPS · Full GPU', color: '#f97316' },
];

export function PerformanceMode({ defaultMode = 'balanced', onChange }: PerformanceModeProps) {
  const [active, setActive] = useState(defaultMode);

  const handleChange = (id: string) => {
    setActive(id);
    onChange?.(id);
  };

  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 12 }}>Performance Mode</h3>
      <div style={{ display: 'flex', gap: 10 }}>
        {MODES.map((mode) => (
          <motion.button
            key={mode.id}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => handleChange(mode.id)}
            style={{
              flex: 1, padding: '16px 14px', borderRadius: 'var(--radius-md)',
              background: active === mode.id ? 'var(--surface-hover)' : 'var(--surface)',
              border: `2px solid ${active === mode.id ? mode.color : 'transparent'}`,
              cursor: 'pointer', textAlign: 'center',
              transition: 'border-color 0.3s, background 0.3s',
            }}
          >
            <div className="font-semibold" style={{ fontSize: '0.9rem', marginBottom: 4 }}>
              {mode.label}
            </div>
            <div className="text-xs" style={{ color: 'var(--text-tertiary)' }}>{mode.desc}</div>
            {active === mode.id && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-xs"
                style={{
                  marginTop: 8, padding: '3px 10px', borderRadius: 10,
                  background: `${mode.color}20`, color: mode.color,
                  display: 'inline-block', fontWeight: 700,
                }}
              >
                Active
              </motion.div>
            )}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
