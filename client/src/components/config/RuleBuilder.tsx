/**
 * VisionX — RuleBuilder Component
 * Visual rule definition: IF trigger → THEN action
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GlowButton } from '../ui/GlowButton';

interface Rule {
  id: string;
  name: string;
  trigger: string;
  action: string;
  enabled: boolean;
}

interface RuleBuilderProps {
  rules: Rule[];
  onSave?: (rule: Rule) => void;
  onToggle?: (id: string) => void;
}

export function RuleBuilder({ rules, onSave, onToggle }: RuleBuilderProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTrigger, setNewTrigger] = useState('');
  const [newAction, setNewAction] = useState('');

  const handleSave = () => {
    if (!newName || !newTrigger || !newAction) return;
    onSave?.({
      id: Date.now().toString(),
      name: newName,
      trigger: newTrigger,
      action: newAction,
      enabled: true,
    });
    setNewName('');
    setNewTrigger('');
    setNewAction('');
    setIsCreating(false);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3 className="font-semibold">Automation Rules</h3>
        <GlowButton size="sm" onClick={() => setIsCreating(!isCreating)}>
          {isCreating ? '✕ Cancel' : '+ New Rule'}
        </GlowButton>
      </div>

      {isCreating && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="glass-card"
          style={{ marginBottom: 16, padding: 16 }}
        >
          <input
            value={newName} onChange={(e) => setNewName(e.target.value)}
            placeholder="Rule name..."
            style={{
              width: '100%', padding: 10, marginBottom: 10, borderRadius: 'var(--radius-sm)',
              background: 'var(--surface)', border: '1px solid var(--border)',
              color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none',
              fontFamily: 'var(--font-sans)',
            }}
          />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--success)', marginBottom: 4, display: 'block' }}>
                IF (Trigger)
              </label>
              <input
                value={newTrigger} onChange={(e) => setNewTrigger(e.target.value)}
                placeholder="e.g. Person count > 5"
                style={{
                  width: '100%', padding: 10, borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>
            <div>
              <label className="text-xs font-medium" style={{ color: 'var(--accent)', marginBottom: 4, display: 'block' }}>
                THEN (Action)
              </label>
              <input
                value={newAction} onChange={(e) => setNewAction(e.target.value)}
                placeholder="e.g. Send email alert"
                style={{
                  width: '100%', padding: 10, borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface)', border: '1px solid var(--border)',
                  color: 'var(--text-primary)', fontSize: '0.8rem', outline: 'none',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>
          </div>
          <GlowButton size="sm" onClick={handleSave}>Save Rule</GlowButton>
        </motion.div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {rules.map((rule) => (
          <div key={rule.id} className="glass-subtle" style={{
            padding: '14px 16px', borderRadius: 'var(--radius-sm)',
            opacity: rule.enabled ? 1 : 0.5,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          }}>
            <div>
              <span className="font-medium text-sm">{rule.name}</span>
              <div className="text-xs" style={{ color: 'var(--text-tertiary)', marginTop: 4 }}>
                IF {rule.trigger} → THEN {rule.action}
              </div>
            </div>
            <button
              onClick={() => onToggle?.(rule.id)}
              style={{
                width: 44, height: 24, borderRadius: 12, border: 'none', cursor: 'pointer',
                background: rule.enabled ? 'var(--accent)' : 'var(--surface)', position: 'relative',
              }}
            >
              <div style={{
                width: 18, height: 18, borderRadius: '50%', background: '#fff',
                position: 'absolute', top: 3, left: rule.enabled ? 23 : 3,
                transition: 'left 0.2s',
              }} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
