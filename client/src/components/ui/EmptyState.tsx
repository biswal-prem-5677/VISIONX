/**
 * VisionX — Empty State Component
 * Shown when no data is available
 */

import { motion } from 'framer-motion';
import { GlowButton } from './GlowButton';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon = '📭',
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: 60, textAlign: 'center',
      }}
    >
      <span style={{ fontSize: 56, marginBottom: 16 }}>{icon}</span>
      <h3 className="font-semibold" style={{ fontSize: '1.2rem', marginBottom: 8 }}>
        {title}
      </h3>
      {description && (
        <p className="text-sm" style={{
          color: 'var(--text-secondary)', maxWidth: 360, lineHeight: 1.6, marginBottom: 20,
        }}>
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <GlowButton onClick={onAction}>{actionLabel}</GlowButton>
      )}
    </motion.div>
  );
}
