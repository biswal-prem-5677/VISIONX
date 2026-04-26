/**
 * VisionX — EnergyField Effect
 * ========================================
 * Reactive energy shield/aura behind the character.
 * Pulses on detection events, ripples on alerts.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Mesh } from 'three';

interface EnergyFieldProps {
  color: string;
  intensity?: number;
  reactive?: boolean;
  pulseSpeed?: number;
}

export function EnergyField({
  color, intensity = 0.15, reactive: _reactive = true, pulseSpeed = 1,
}: EnergyFieldProps) {
  const fieldRef = useRef<Mesh>(null);
  const innerRef = useRef<Mesh>(null);
  const ringRef = useRef<Mesh>(null);

  const fieldMat = useMemo(() => new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.4,
    transparent: true,
    opacity: intensity,
    side: THREE.DoubleSide,
    wireframe: true,
  }), [color, intensity]);

  const innerMat = useMemo(() => new THREE.MeshStandardMaterial({
    color,
    emissive: color,
    emissiveIntensity: 0.6,
    transparent: true,
    opacity: intensity * 0.5,
    side: THREE.BackSide,
  }), [color, intensity]);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime() * pulseSpeed;

    if (fieldRef.current) {
      // Breathing pulse
      const pulse = 1 + Math.sin(t * 0.8) * 0.03;
      fieldRef.current.scale.setScalar(pulse);
      fieldRef.current.rotation.y = t * 0.15;
      fieldRef.current.rotation.x = Math.sin(t * 0.3) * 0.05;

      // Opacity pulse
      fieldMat.opacity = intensity + Math.sin(t * 1.5) * 0.05;
    }

    if (innerRef.current) {
      innerRef.current.rotation.y = -t * 0.1;
      innerRef.current.scale.setScalar(0.95 + Math.sin(t * 1.2) * 0.02);
    }

    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.4;
      ringRef.current.rotation.x = Math.PI / 2 + Math.sin(t * 0.5) * 0.1;
      const ringPulse = 0.08 + Math.sin(t * 2) * 0.03;
      (ringRef.current.material as THREE.MeshStandardMaterial).opacity = ringPulse;
    }
  });

  return (
    <group position={[0, 0.2, -0.2]}>
      {/* Outer wireframe field */}
      <mesh ref={fieldRef}>
        <icosahedronGeometry args={[0.9, 1]} />
        <primitive object={fieldMat} attach="material" />
      </mesh>

      {/* Inner smooth field */}
      <mesh ref={innerRef}>
        <sphereGeometry args={[0.85, 16, 16]} />
        <primitive object={innerMat} attach="material" />
      </mesh>

      {/* Equatorial energy ring */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.95, 0.01, 8, 64]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1}
          transparent
          opacity={0.1}
        />
      </mesh>
    </group>
  );
}
