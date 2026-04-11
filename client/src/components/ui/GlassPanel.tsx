/**
 * VisionX — GlassPanel Component
 * Core glassmorphic container component
 */

import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  glow?: boolean;
  hover?: boolean;
  padding?: string;
  onClick?: () => void;
}

export function GlassPanel({
  children,
  className = '',
  style,
  glow = false,
  hover = true,
  padding = '20px',
  onClick,
}: GlassPanelProps) {
  return (
    <motion.div
      className={`glass ${glow ? 'glow-border' : ''} ${className}`}
      style={{
        padding,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'border-color var(--transition-base), box-shadow var(--transition-base)',
        ...style,
      }}
      onClick={onClick}
      whileHover={hover ? { scale: 1.005, borderColor: 'var(--border-hover)' } : undefined}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
