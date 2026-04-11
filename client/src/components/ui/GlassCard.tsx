/**
 * VisionX — GlassCard Component
 * Flexible glassmorphic card — supports children OR stat-card mode
 */

import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';
import './GlassCard.css';

interface GlassCardProps {
  children?: ReactNode;
  title?: string;
  value?: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: { value: number; label: string };
  accentColor?: string;
  delay?: number;
  className?: string;
  style?: CSSProperties;
}

export function GlassCard({
  children,
  title,
  value,
  subtitle,
  icon,
  trend,
  accentColor,
  delay = 0,
  className = '',
  style,
}: GlassCardProps) {
  // If children are provided, render as flexible container
  if (children) {
    return (
      <motion.div
        className={`glass-card ${className}`}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, delay, type: 'spring', stiffness: 100 }}
        style={style}
      >
        {children}
      </motion.div>
    );
  }

  // Stat card mode
  return (
    <motion.div
      className={`glass-card ${className}`}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, delay, type: 'spring', stiffness: 100 }}
      whileHover={{ scale: 1.02, y: -2 }}
      style={style}
    >
      <div className="glass-card__header">
        <span className="glass-card__title">{title}</span>
        {icon && (
          <div className="glass-card__icon" style={accentColor ? { color: accentColor } : {}}>
            {icon}
          </div>
        )}
      </div>

      <div className="glass-card__value" style={accentColor ? { color: accentColor } : {}}>
        {value}
      </div>

      <div className="glass-card__footer">
        {subtitle && <span className="glass-card__subtitle">{subtitle}</span>}
        {trend && (
          <span className={`glass-card__trend ${trend.value >= 0 ? 'positive' : 'negative'}`}>
            {trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}% {trend.label}
          </span>
        )}
      </div>
    </motion.div>
  );
}
