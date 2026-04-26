/**
 * VisionX — ThemeTransition Effect
 * ========================================
 * Smooth visual transition when switching themes.
 * Character dissolves into particles and reforms as new archetype.
 */

import { useRef, useState, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ThemeTransitionProps {
  isTransitioning: boolean;
  color: string;
  onTransitionComplete?: () => void;
}

export function ThemeTransition({
  isTransitioning, color, onTransitionComplete,
}: ThemeTransitionProps) {
  const groupRef = useRef<THREE.Group>(null);
  const progressRef = useRef(0);
  const [active, setActive] = useState(false);

  useEffect(() => {
    if (isTransitioning) {
      setActive(true);
      progressRef.current = 0;
    }
  }, [isTransitioning]);

  useFrame(() => {
    if (!active || !groupRef.current) return;

    progressRef.current += 0.02;

    if (progressRef.current < 0.5) {
      // Phase 1: Expand and fade out (dissolve)
      const expand = progressRef.current * 2;
      groupRef.current.scale.setScalar(1 + expand * 2);
      groupRef.current.children.forEach((child) => {
        if ((child as THREE.Mesh).material) {
          const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
          mat.opacity = 1 - expand;
        }
      });
      groupRef.current.rotation.y += 0.05;
    } else if (progressRef.current < 1) {
      // Phase 2: Contract and fade in (reform)
      const contract = (progressRef.current - 0.5) * 2;
      groupRef.current.scale.setScalar(3 - contract * 2);
      groupRef.current.children.forEach((child) => {
        if ((child as THREE.Mesh).material) {
          const mat = (child as THREE.Mesh).material as THREE.MeshStandardMaterial;
          mat.opacity = contract * 0.6;
        }
      });
      groupRef.current.rotation.y += 0.03;
    } else {
      // Complete
      setActive(false);
      progressRef.current = 0;
      onTransitionComplete?.();
    }
  });

  if (!active) return null;

  return (
    <group ref={groupRef} position={[0, 0.3, 0]}>
      {/* Transition burst particles */}
      {[...Array(12)].map((_, i) => {
        const angle = (i / 12) * Math.PI * 2;
        return (
          <mesh
            key={i}
            position={[
              Math.cos(angle) * 0.4,
              Math.sin(angle * 2) * 0.2,
              Math.sin(angle) * 0.4,
            ]}
          >
            <octahedronGeometry args={[0.03 + Math.random() * 0.03]} />
            <meshStandardMaterial
              color={color}
              emissive={color}
              emissiveIntensity={1.5}
              transparent
              opacity={0.6}
            />
          </mesh>
        );
      })}

      {/* Central flash */}
      <mesh>
        <sphereGeometry args={[0.15, 8, 8]} />
        <meshStandardMaterial
          color="#ffffff"
          emissive={color}
          emissiveIntensity={2}
          transparent
          opacity={0.4}
        />
      </mesh>
    </group>
  );
}
