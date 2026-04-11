/**
 * VisionX — Loading State Component
 * Skeleton/shimmer loading placeholder
 */

import { motion } from 'framer-motion';

interface LoadingStateProps {
  lines?: number;
  type?: 'card' | 'list' | 'chart' | 'full';
}

export function LoadingState({ lines = 3, type = 'card' }: LoadingStateProps) {
  if (type === 'full') {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        minHeight: 400, flexDirection: 'column', gap: 16,
      }}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          style={{
            width: 40, height: 40, borderRadius: '50%',
            border: '3px solid var(--border)',
            borderTopColor: 'var(--accent)',
          }}
        />
        <span className="text-sm" style={{ color: 'var(--text-tertiary)' }}>Loading...</span>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, padding: 20 }}>
      {type === 'chart' && (
        <motion.div
          className="shimmer"
          style={{ height: 200, borderRadius: 'var(--radius-md)', background: 'var(--surface)' }}
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
      {Array.from({ length: lines }).map((_, i) => (
        <motion.div
          key={i}
          style={{
            height: type === 'list' ? 48 : 16,
            borderRadius: type === 'list' ? 'var(--radius-sm)' : 4,
            background: 'var(--surface)',
            width: i === lines - 1 ? '60%' : '100%',
          }}
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.1 }}
        />
      ))}
    </div>
  );
}
