/**
 * VisionX — Gaze Tracker 3D Component
 * A 3D element that follows the user's cursor/gaze
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Mesh } from 'three';
import * as THREE from 'three';

interface GazeTrackerProps {
  gazeX?: number; // -1 to 1
  gazeY?: number; // -1 to 1
  color?: string;
}

export function GazeTracker({ gazeX = 0, gazeY = 0, color = '#a78bfa' }: GazeTrackerProps) {
  const meshRef = useRef<Mesh>(null);
  const targetPos = useRef(new THREE.Vector3(0, 0, 0));

  useFrame(() => {
    if (!meshRef.current) return;

    // Map gaze to 3D position
    targetPos.current.set(gazeX * 3, -gazeY * 2, 2);

    // Smooth lerp
    meshRef.current.position.lerp(targetPos.current, 0.05);

    // Look at camera
    meshRef.current.lookAt(0, 0, 8);

    // Subtle pulse
    const scale = 1 + Math.sin(Date.now() * 0.003) * 0.05;
    meshRef.current.scale.setScalar(scale);
  });

  return (
    <mesh ref={meshRef} position={[0, 0, 2]}>
      <ringGeometry args={[0.15, 0.2, 32]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.6}
        transparent
        opacity={0.4}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}
