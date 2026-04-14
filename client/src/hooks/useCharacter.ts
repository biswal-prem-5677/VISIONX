/**
 * VisionX — useCharacter Hook
 * ========================================
 * Connects theme store, event store, gaze, and idle timer to the character system.
 * This is the integration brain — it makes the character feel alive.
 */

import { useEffect, useRef, useCallback } from 'react';
import { useCharacterStore, THEME_TO_ARCHETYPE } from '../stores/characterStore';
import { useThemeStore } from '../stores/themeStore';
import { useGaze } from './useGaze';
import type { Expression, Gesture, IdleState } from '../stores/characterStore';

const IDLE_TIMEOUT = 30_000;      // 30s → idle
const BORED_TIMEOUT = 50_000;     // 50s → bored
const SLEEPING_TIMEOUT = 80_000;  // 80s → sleeping

export function useCharacter() {
  const theme = useThemeStore((s) => s.theme);
  const {
    archetype, expression, idleState, gesture, visible, scale, lipSyncValue,
    setArchetype, setExpression, setIdleState, setGesture,
    lastInteractionTime, recordInteraction, getConfig,
  } = useCharacterStore();

  const gaze = useGaze();
  const idleTimerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  // Sync archetype with theme
  useEffect(() => {
    const newArchetype = THEME_TO_ARCHETYPE[theme];
    if (newArchetype && newArchetype !== archetype) {
      setArchetype(newArchetype);
    }
  }, [theme, archetype, setArchetype]);

  // Idle state machine
  useEffect(() => {
    idleTimerRef.current = setInterval(() => {
      const elapsed = Date.now() - lastInteractionTime;

      if (elapsed > SLEEPING_TIMEOUT) {
        setIdleState('sleeping');
        setExpression('sleeping');
      } else if (elapsed > BORED_TIMEOUT) {
        setIdleState('bored');
      } else if (elapsed > IDLE_TIMEOUT) {
        setIdleState('idle');
      }
    }, 2000);

    return () => {
      if (idleTimerRef.current) clearInterval(idleTimerRef.current);
    };
  }, [lastInteractionTime, setIdleState, setExpression]);

  // Wake up on mouse movement
  useEffect(() => {
    if (gaze.isActive && idleState !== 'active') {
      recordInteraction();
      setExpression('neutral');
    }
  }, [gaze.isActive, gaze.x, gaze.y, idleState, recordInteraction, setExpression]);

  // Trigger expressions from system events
  const triggerAlert = useCallback(() => {
    setExpression('alert');
    setGesture('alert');
    setTimeout(() => {
      setExpression('neutral');
      setGesture('none');
    }, 3000);
  }, [setExpression, setGesture]);

  const triggerHappy = useCallback(() => {
    setExpression('happy');
    setGesture('thumbsUp');
    setTimeout(() => {
      setExpression('neutral');
      setGesture('none');
    }, 2000);
  }, [setExpression, setGesture]);

  const triggerSurprise = useCallback(() => {
    setExpression('surprised');
    setTimeout(() => setExpression('neutral'), 2000);
  }, [setExpression]);

  const triggerWave = useCallback(() => {
    setGesture('wave');
    setExpression('happy');
    setTimeout(() => {
      setGesture('none');
      setExpression('neutral');
    }, 2500);
  }, [setGesture, setExpression]);

  const triggerPoint = useCallback((direction?: 'left' | 'right' | 'up') => {
    setGesture('point');
    setTimeout(() => setGesture('none'), 2000);
  }, [setGesture]);

  return {
    // State
    archetype,
    expression,
    idleState,
    gesture,
    visible,
    scale,
    lipSyncValue,
    gaze,
    config: getConfig(),

    // Triggers
    triggerAlert,
    triggerHappy,
    triggerSurprise,
    triggerWave,
    triggerPoint,
    recordInteraction,
  };
}
