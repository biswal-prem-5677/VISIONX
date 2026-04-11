/**
 * VisionX — Animated Background
 * Theme-specific animated 3D background effects
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Mesh } from 'three';

const THEME_COLORS: Record<string, { primary: string; secondary: string }> = {
  obsidian: { primary: '#8b5cf6', secondary: '#6d28d9' },
  cyber: { primary: '#06b6d4', secondary: '#0891b2' },
  aurora: { primary: '#10b981', secondary: '#059669' },
  ember: { primary: '#f97316', secondary: '#ea580c' },
  matrix: { primary: '#22c55e', secondary: '#16a34a' },
};

interface BackgroundProps {
  theme?: string;
}

function GlowOrb({ position, color, scale = 1, speed = 0.5 }: {
  position: [number, number, number];
  color: string;
  scale?: number;
  speed?: number;
}) {
  const meshRef = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * speed;
    meshRef.current.position.y = position[1] + Math.sin(t) * 0.5;
    meshRef.current.position.x = position[0] + Math.cos(t * 0.7) * 0.3;
    meshRef.current.scale.setScalar(scale + Math.sin(t * 1.5) * 0.1);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[0.8, 16, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.4}
        transparent
        opacity={0.15}
        roughness={0.9}
      />
    </mesh>
  );
}

function GridPlane({ color }: { color: string }) {
  const meshRef = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    meshRef.current.rotation.x = -Math.PI / 2;
    meshRef.current.position.y = -3 + Math.sin(clock.getElapsedTime() * 0.2) * 0.1;
  });

  return (
    <mesh ref={meshRef} position={[0, -3, 0]}>
      <planeGeometry args={[40, 40, 20, 20]} />
      <meshStandardMaterial
        color={color}
        wireframe
        transparent
        opacity={0.06}
      />
    </mesh>
  );
}

export function AnimatedBackground({ theme = 'obsidian' }: BackgroundProps) {
  const colors = THEME_COLORS[theme] || THEME_COLORS.obsidian;

  return (
    <group>
      {/* Ambient glow orbs */}
      <GlowOrb position={[-5, 2, -5]} color={colors.primary} scale={1.5} speed={0.3} />
      <GlowOrb position={[4, -1, -8]} color={colors.secondary} scale={2} speed={0.4} />
      <GlowOrb position={[0, 3, -6]} color={colors.primary} scale={1} speed={0.6} />
      <GlowOrb position={[-3, -2, -4]} color={colors.secondary} scale={0.8} speed={0.5} />

      {/* Grid floor */}
      <GridPlane color={colors.primary} />
    </group>
  );
}
