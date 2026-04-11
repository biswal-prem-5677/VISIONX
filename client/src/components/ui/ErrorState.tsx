/**
 * VisionX — Error State Component
 * Shown when an API call or operation fails
 */

import { motion } from 'framer-motion';
import { GlowButton } from './GlowButton';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  onRetry,
}: ErrorStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: 60, textAlign: 'center',
      }}
    >
      <div style={{
        width: 64, height: 64, borderRadius: '50%',
        background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 28, marginBottom: 16,
      }}>
        ⚠️
      </div>
      <h3 className="font-semibold" style={{ fontSize: '1.2rem', marginBottom: 8 }}>
        {title}
      </h3>
      <p className="text-sm" style={{
        color: 'var(--text-secondary)', maxWidth: 360, lineHeight: 1.6, marginBottom: 20,
      }}>
        {message}
      </p>
      {onRetry && (
        <GlowButton variant="secondary" onClick={onRetry}>Retry</GlowButton>
      )}
    </motion.div>
  );
}
