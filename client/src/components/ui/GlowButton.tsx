/**
 * VisionX — GlowButton Component
 */

import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';
import './GlowButton.css';

interface GlowButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: ReactNode;
  disabled?: boolean;
  fullWidth?: boolean;
  style?: CSSProperties;
}

export function GlowButton({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  icon,
  disabled = false,
  fullWidth = false,
  style,
}: GlowButtonProps) {
  return (
    <motion.button
      className={`glow-btn glow-btn--${variant} glow-btn--${size} ${fullWidth ? 'glow-btn--full' : ''}`}
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      transition={{ type: 'spring', stiffness: 400, damping: 17 }}
      style={style}
    >
      {icon && <span className="glow-btn__icon">{icon}</span>}
      {children}
    </motion.button>
  );
}
