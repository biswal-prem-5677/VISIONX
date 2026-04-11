/**
 * VisionX — AutomationBuilder Component
 * "If this → do this" visual builder with trigger/action templates
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

const TRIGGER_TEMPLATES = [
  { id: 't1', label: 'Person count exceeds', icon: '👥', placeholder: '5' },
  { id: 't2', label: 'Object enters zone', icon: '📍', placeholder: 'Zone A' },
  { id: 't3', label: 'No motion for duration', icon: '⏱️', placeholder: '30s' },
  { id: 't4', label: 'Specific object detected', icon: '🎯', placeholder: 'Vehicle' },
  { id: 't5', label: 'Camera disconnected', icon: '📹', placeholder: '' },
];

const ACTION_TEMPLATES = [
  { id: 'a1', label: 'Send email alert', icon: '📧' },
  { id: 'a2', label: 'Push notification', icon: '🔔' },
  { id: 'a3', label: 'Sound alarm', icon: '🔊' },
  { id: 'a4', label: 'Save snapshot', icon: '📸' },
  { id: 'a5', label: 'Webhook POST', icon: '🌐' },
  { id: 'a6', label: 'Record video clip', icon: '🎬' },
];

interface AutomationBuilderProps {
  onSave?: (trigger: string, actions: string[]) => void;
}

export function AutomationBuilder({ onSave }: AutomationBuilderProps) {
  const [selectedTrigger, setSelectedTrigger] = useState<string | null>(null);
  const [selectedActions, setSelectedActions] = useState<string[]>([]);
  const [triggerValue, setTriggerValue] = useState('');

  const toggleAction = (id: string) => {
    setSelectedActions((s) =>
      s.includes(id) ? s.filter((a) => a !== id) : [...s, id]
    );
  };

  const handleSave = () => {
    if (!selectedTrigger || selectedActions.length === 0) return;
    const trigger = TRIGGER_TEMPLATES.find((t) => t.id === selectedTrigger);
    const actions = ACTION_TEMPLATES.filter((a) => selectedActions.includes(a.id));
    onSave?.(
      `${trigger?.label} ${triggerValue}`.trim(),
      actions.map((a) => a.label),
    );
    setSelectedTrigger(null);
    setSelectedActions([]);
    setTriggerValue('');
  };

  return (
    <div>
      {/* Triggers */}
      <h4 className="font-semibold text-sm" style={{ color: 'var(--success)', marginBottom: 10 }}>
        IF (Select Trigger)
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 20 }}>
        {TRIGGER_TEMPLATES.map((t) => (
          <motion.button
            key={t.id}
            whileTap={{ scale: 0.98 }}
            onClick={() => setSelectedTrigger(t.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
              background: selectedTrigger === t.id ? 'rgba(34,197,94,0.1)' : 'var(--surface)',
              border: `1px solid ${selectedTrigger === t.id ? 'var(--success)' : 'var(--border)'}`,
              cursor: 'pointer', textAlign: 'left', color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <span>{t.icon}</span>
            <span className="text-sm">{t.label}</span>
            {selectedTrigger === t.id && t.placeholder && (
              <input
                value={triggerValue}
                onChange={(e) => setTriggerValue(e.target.value)}
                placeholder={t.placeholder}
                style={{
                  marginLeft: 'auto', width: 80, padding: '4px 8px',
                  borderRadius: 4, background: 'var(--surface)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none',
                  fontFamily: 'var(--font-sans)',
                }}
                onClick={(e) => e.stopPropagation()}
              />
            )}
          </motion.button>
        ))}
      </div>

      {/* Actions */}
      <h4 className="font-semibold text-sm" style={{ color: 'var(--accent)', marginBottom: 10 }}>
        THEN (Select Actions)
      </h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 20 }}>
        {ACTION_TEMPLATES.map((a) => (
          <motion.button
            key={a.id}
            whileTap={{ scale: 0.98 }}
            onClick={() => toggleAction(a.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '10px 14px', borderRadius: 'var(--radius-sm)',
              background: selectedActions.includes(a.id) ? 'rgba(139,92,246,0.1)' : 'var(--surface)',
              border: `1px solid ${selectedActions.includes(a.id) ? 'var(--accent)' : 'var(--border)'}`,
              cursor: 'pointer', color: 'var(--text-primary)',
              fontFamily: 'var(--font-sans)',
            }}
          >
            <span>{a.icon}</span>
            <span className="text-sm">{a.label}</span>
          </motion.button>
        ))}
      </div>

      <GlowButton onClick={handleSave} disabled={!selectedTrigger || selectedActions.length === 0}>
        Create Rule
      </GlowButton>
    </div>
  );
}
