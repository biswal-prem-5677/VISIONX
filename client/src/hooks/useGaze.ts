/**
 * VisionX — Gaze Tracking Hook
 * Tracks cursor position for 3D parallax and character gaze
 */

import { useState, useEffect, useCallback } from 'react';

interface GazeState {
  x: number; // -1 to 1 (left to right)
  y: number; // -1 to 1 (top to bottom)
  rawX: number;
  rawY: number;
  isActive: boolean;
}

export function useGaze() {
  const [gaze, setGaze] = useState<GazeState>({
    x: 0, y: 0, rawX: 0, rawY: 0, isActive: false,
  });

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const x = (e.clientX / window.innerWidth) * 2 - 1;
    const y = (e.clientY / window.innerHeight) * 2 - 1;
    setGaze({ x, y, rawX: e.clientX, rawY: e.clientY, isActive: true });
  }, []);

  const handleMouseLeave = useCallback(() => {
    setGaze((s) => ({ ...s, isActive: false }));
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [handleMouseMove, handleMouseLeave]);

  return gaze;
}
