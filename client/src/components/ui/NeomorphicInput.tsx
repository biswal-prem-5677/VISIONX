/**
 * VisionX — Neomorphic Input Component
 * Premium neumorphic-style input fields
 */

import { useState } from 'react';
import type { CSSProperties, InputHTMLAttributes } from 'react';

interface NeomorphicInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'style'> {
  label?: string;
  icon?: string;
  error?: string;
  style?: CSSProperties;
}

export function NeomorphicInput({
  label,
  icon,
  error,
  style,
  ...props
}: NeomorphicInputProps) {
  const [focused, setFocused] = useState(false);

  return (
    <div style={{ ...style, display: 'flex', flexDirection: 'column', gap: 6 }}>
      {label && (
        <label className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
          {label}
        </label>
      )}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '12px 16px', borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: `1px solid ${error ? 'var(--danger)' : focused ? 'var(--accent)' : 'var(--border)'}`,
        boxShadow: focused
          ? '0 0 0 3px rgba(var(--accent-rgb, 139,92,246), 0.15), inset 0 2px 4px rgba(0,0,0,0.1)'
          : 'inset 0 2px 4px rgba(0,0,0,0.1)',
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}>
        {icon && <span style={{ opacity: 0.5, fontSize: 16 }}>{icon}</span>}
        <input
          {...props}
          onFocus={(e) => { setFocused(true); props.onFocus?.(e); }}
          onBlur={(e) => { setFocused(false); props.onBlur?.(e); }}
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: 'var(--text-primary)', fontSize: '0.9rem',
            fontFamily: 'var(--font-sans)',
          }}
        />
      </div>
      {error && (
        <span className="text-xs" style={{ color: 'var(--danger)' }}>{error}</span>
      )}
    </div>
  );
}
