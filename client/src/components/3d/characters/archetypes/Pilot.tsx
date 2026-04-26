/**
 * VisionX — Pilot Archetype (Ember Theme)
 * Tech-focused, holographic visor, sharp movements, orange energy, mechanical parts.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Mesh } from 'three';
import { CharacterModel, type CharacterProps } from '../CharacterModel';

interface PilotProps extends Omit<CharacterProps, 'primaryColor' | 'secondaryColor' | 'emissiveColor'> {}

export function Pilot(props: PilotProps) {
  const visorRef = useRef<Mesh>(null);
  const gearRef1 = useRef<Mesh>(null);
  const gearRef2 = useRef<Mesh>(null);
  const thrusterRef = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (visorRef.current) {
      (visorRef.current.material as THREE.MeshStandardMaterial).opacity =
        0.5 + Math.sin(t * 3) * 0.15;
    }
    if (gearRef1.current) {
      gearRef1.current.rotation.z = t * 2;
    }
    if (gearRef2.current) {
      gearRef2.current.rotation.z = -t * 1.5;
    }
    if (thrusterRef.current) {
      const flicker = 0.6 + Math.random() * 0.3;
      thrusterRef.current.scale.y = flicker;
      (thrusterRef.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        1.5 + Math.sin(t * 10) * 0.5;
    }
  });

  return (
    <group>
      <CharacterModel
        {...props}
        primaryColor="#1c0a00"
        secondaryColor="#ea580c"
        emissiveColor="#fb923c"
        breathingSpeed={1.0}
        gazeInfluence={1.0}
      />
      {/* Holographic visor */}
      <mesh ref={visorRef} position={[0, 0.92, 0.28]} rotation={[0.1, 0, 0]}>
        <planeGeometry args={[0.35, 0.1]} />
        <meshStandardMaterial
          color="#fb923c" emissive="#f97316" emissiveIntensity={0.8}
          transparent opacity={0.5} side={THREE.DoubleSide}
        />
      </mesh>
      {/* Mechanical gears on shoulders */}
      <mesh ref={gearRef1} position={[-0.38, 0.42, 0]}>
        <torusGeometry args={[0.05, 0.012, 4, 8]} />
        <meshStandardMaterial color="#fb923c" emissive="#ea580c" emissiveIntensity={0.6} metalness={0.9} />
      </mesh>
      <mesh ref={gearRef2} position={[0.38, 0.42, 0]}>
        <torusGeometry args={[0.04, 0.01, 4, 8]} />
        <meshStandardMaterial color="#fb923c" emissive="#ea580c" emissiveIntensity={0.6} metalness={0.9} />
      </mesh>
      {/* Thruster exhaust */}
      <mesh ref={thrusterRef} position={[0, -0.5, -0.1]}>
        <coneGeometry args={[0.08, 0.25, 8]} />
        <meshStandardMaterial color="#fbbf24" emissive="#f97316" emissiveIntensity={1.5} transparent opacity={0.4} />
      </mesh>
    </group>
  );
}
