/**
 * VisionX — Haptic Feedback Hook
 * Web Haptics API for tactile feedback on interactions
 */

import { useCallback } from 'react';

type HapticPattern = 'tap' | 'success' | 'warning' | 'error' | 'heavy';

const PATTERNS: Record<HapticPattern, number[]> = {
  tap: [10],
  success: [10, 50, 10],
  warning: [30, 50, 30],
  error: [50, 30, 50, 30, 50],
  heavy: [80],
};

export function useHaptics() {
  const supportsHaptics = 'vibrate' in navigator;

  const vibrate = useCallback((pattern: HapticPattern = 'tap') => {
    if (!supportsHaptics) return;
    try {
      navigator.vibrate(PATTERNS[pattern]);
    } catch { /* unsupported context */ }
  }, [supportsHaptics]);

  const vibrateCustom = useCallback((pattern: number[]) => {
    if (!supportsHaptics) return;
    try {
      navigator.vibrate(pattern);
    } catch { /* unsupported context */ }
  }, [supportsHaptics]);

  const stop = useCallback(() => {
    if (!supportsHaptics) return;
    navigator.vibrate(0);
  }, [supportsHaptics]);

  return { vibrate, vibrateCustom, stop, supportsHaptics };
}
