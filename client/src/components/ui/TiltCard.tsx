/**
 * VisionX — TiltCard Component
 * Parallax hover tilt effect for premium card interactions
 */

import { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import type { CSSProperties, ReactNode } from 'react';

interface TiltCardProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  tiltAmount?: number;
  glareEnabled?: boolean;
}

export function TiltCard({
  children,
  className = '',
  style,
  tiltAmount = 10,
  glareEnabled = true,
}: TiltCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const [glare, setGlare] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;

    setTilt({
      x: (y - 0.5) * tiltAmount * -1,
      y: (x - 0.5) * tiltAmount,
    });

    if (glareEnabled) {
      setGlare({ x: x * 100, y: y * 100, opacity: 0.15 });
    }
  };

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 });
    setGlare({ x: 50, y: 50, opacity: 0 });
  };

  return (
    <motion.div
      ref={cardRef}
      className={`glass-card ${className}`}
      style={{
        ...style,
        transformStyle: 'preserve-3d',
        perspective: 1000,
      }}
      animate={{
        rotateX: tilt.x,
        rotateY: tilt.y,
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {glareEnabled && (
        <div
          style={{
            position: 'absolute', inset: 0, borderRadius: 'inherit',
            pointerEvents: 'none',
            background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255,255,255,${glare.opacity}), transparent 60%)`,
            transition: 'opacity 0.2s',
          }}
        />
      )}
    </motion.div>
  );
}
