/**
 * VisionX — Floating 3D Objects
 * Ambient geometric shapes that drift around the scene
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Mesh } from 'three';

const THEME_COLORS: Record<string, string[]> = {
  obsidian: ['#8b5cf6', '#a78bfa', '#6d28d9'],
  cyber: ['#06b6d4', '#22d3ee', '#0891b2'],
  aurora: ['#10b981', '#34d399', '#059669'],
  ember: ['#f97316', '#fb923c', '#ea580c'],
  matrix: ['#22c55e', '#4ade80', '#16a34a'],
};

interface FloatingObjectProps {
  position: [number, number, number];
  color: string;
  shape: 'box' | 'octahedron' | 'torus' | 'icosahedron';
  speed: number;
  rotationSpeed: number;
  scale: number;
}

function FloatingObject({ position, color, shape, speed, rotationSpeed, scale }: FloatingObjectProps) {
  const meshRef = useRef<Mesh>(null);
  const offset = useMemo(() => Math.random() * Math.PI * 2, []);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;
    const t = clock.getElapsedTime() * speed + offset;

    meshRef.current.position.y = position[1] + Math.sin(t) * 1.5;
    meshRef.current.position.x = position[0] + Math.cos(t * 0.5) * 0.5;
    meshRef.current.rotation.x += rotationSpeed * 0.01;
    meshRef.current.rotation.y += rotationSpeed * 0.015;
    meshRef.current.rotation.z += rotationSpeed * 0.008;
  });

  const geometry = useMemo(() => {
    switch (shape) {
      case 'octahedron': return <octahedronGeometry args={[0.4]} />;
      case 'torus': return <torusGeometry args={[0.3, 0.12, 8, 16]} />;
      case 'icosahedron': return <icosahedronGeometry args={[0.35, 0]} />;
      default: return <boxGeometry args={[0.4, 0.4, 0.4]} />;
    }
  }, [shape]);

  return (
    <mesh ref={meshRef} position={position} scale={scale}>
      {geometry}
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.2}
        transparent
        opacity={0.25}
        wireframe={Math.random() > 0.5}
        roughness={0.8}
      />
    </mesh>
  );
}

interface FloatingObjectsProps {
  count?: number;
  theme?: string;
}

export function FloatingObjects({ count = 15, theme = 'obsidian' }: FloatingObjectsProps) {
  const colors = THEME_COLORS[theme] || THEME_COLORS.obsidian;
  const shapes: FloatingObjectProps['shape'][] = ['box', 'octahedron', 'torus', 'icosahedron'];

  const objects = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      id: i,
      position: [
        (Math.random() - 0.5) * 20,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 15 - 5,
      ] as [number, number, number],
      color: colors[i % colors.length],
      shape: shapes[i % shapes.length],
      speed: 0.2 + Math.random() * 0.4,
      rotationSpeed: 0.5 + Math.random() * 1.5,
      scale: 0.3 + Math.random() * 0.7,
    })),
  [count, colors]);

  return (
    <group>
      {objects.map((obj) => (
        <FloatingObject key={obj.id} {...obj} />
      ))}
    </group>
  );
}
