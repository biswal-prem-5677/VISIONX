/**
 * VisionX — 3D Scene Container
 * ========================================
 * React Three Fiber canvas with:
 * - Animated background effects (per-theme)
 * - Floating geometric objects
 * - AI Character avatar (per-theme archetype)
 * - Particle aura & energy field
 * - Theme transition effects
 */

import { Canvas } from '@react-three/fiber';
import { Environment, Stars } from '@react-three/drei';
import { Suspense, useState, useEffect } from 'react';
import { FloatingObjects } from './FloatingObjects';
import { AnimatedBackground } from './Background';
import { Guardian } from './characters/archetypes/Guardian';
import { Guide } from './characters/archetypes/Guide';
import { Muse } from './characters/archetypes/Muse';
import { Sage } from './characters/archetypes/Sage';
import { Pilot } from './characters/archetypes/Pilot';
import { ParticleAura } from './effects/ParticleAura';
import { EnergyField } from './effects/EnergyField';
import { ThemeTransition } from './effects/ThemeTransition';
import { useCharacterStore, THEME_TO_ARCHETYPE, CHARACTER_CONFIGS } from '../../stores/characterStore';
import { useGaze } from '../../hooks/useGaze';

interface SceneProps {
  theme?: string;
  interactive?: boolean;
}

function CharacterScene({ theme }: { theme: string }) {
  const gaze = useGaze();
  const { expression, idleState, gesture, visible, archetype } = useCharacterStore();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [prevTheme, setPrevTheme] = useState(theme);

  const config = CHARACTER_CONFIGS[archetype];

  // Detect theme change → trigger transition
  useEffect(() => {
    if (theme !== prevTheme) {
      setIsTransitioning(true);
      setPrevTheme(theme);
    }
  }, [theme, prevTheme]);

  // Sync archetype with theme
  useEffect(() => {
    const newArchetype = THEME_TO_ARCHETYPE[theme];
    if (newArchetype) {
      useCharacterStore.getState().setArchetype(newArchetype);
    }
  }, [theme]);

  if (!visible) return null;

  const characterProps = {
    gazeX: gaze.x,
    gazeY: gaze.y,
    expression,
    idleState,
    gesture,
  };

  return (
    <group position={[2.2, -1.5, 0]} scale={1.6}>
      {/* Energy field behind character */}
      <EnergyField color={config.emissiveColor} />

      {/* Character archetype */}
      {archetype === 'guardian' && <Guardian {...characterProps} />}
      {archetype === 'guide' && <Guide {...characterProps} />}
      {archetype === 'muse' && <Muse {...characterProps} />}
      {archetype === 'sage' && <Sage {...characterProps} />}
      {archetype === 'pilot' && <Pilot {...characterProps} />}

      {/* Particle aura */}
      <ParticleAura
        color={config.particleColor}
        archetype={archetype}
        count={50}
        radius={0.9}
      />

      {/* Theme transition effect */}
      <ThemeTransition
        isTransitioning={isTransitioning}
        color={config.emissiveColor}
        onTransitionComplete={() => setIsTransitioning(false)}
      />
    </group>
  );
}

export function Scene({ theme = 'obsidian', interactive = false }: SceneProps) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: -1,
      pointerEvents: interactive ? 'auto' : 'none',
    }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        dpr={[1, 1.5]}
        style={{ background: 'transparent' }}
      >
        <Suspense fallback={null}>
          {/* Lighting */}
          <ambientLight intensity={0.15} />
          <pointLight position={[10, 10, 10]} intensity={0.4} color="#a78bfa" />
          <pointLight position={[-10, -5, 5]} intensity={0.2} color="#38bdf8" />
          <spotLight
            position={[3, 3, 5]}
            intensity={0.3}
            angle={0.4}
            penumbra={0.8}
            color="#ffffff"
          />

          {/* Background effects */}
          <AnimatedBackground theme={theme} />
          <FloatingObjects count={20} theme={theme} />

          {/* Stars */}
          <Stars
            radius={50}
            depth={60}
            count={1500}
            factor={3}
            saturation={0.3}
            fade
            speed={0.5}
          />

          {/* AI Character */}
          <CharacterScene theme={theme} />

          {/* Environment */}
          <Environment preset="night" />
        </Suspense>
      </Canvas>
    </div>
  );
}
