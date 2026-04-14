/**
 * VisionX — Sage Archetype (Matrix Theme)
 * Calm, meditative, green aura, slow breathing, digital rain particles.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Mesh, Group } from 'three';
import { CharacterModel, type CharacterProps } from '../CharacterModel';

interface SageProps extends Omit<CharacterProps, 'primaryColor' | 'secondaryColor' | 'emissiveColor'> {}

export function Sage(props: SageProps) {
  const auraRef = useRef<Mesh>(null);
  const leafRefs = useRef<Mesh[]>([]);
  const leafGroupRef = useRef<Group>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (auraRef.current) {
      const pulse = 0.15 + Math.sin(t * 0.6) * 0.08;
      (auraRef.current.material as THREE.MeshStandardMaterial).opacity = pulse;
      auraRef.current.scale.setScalar(1 + Math.sin(t * 0.4) * 0.05);
      auraRef.current.rotation.y = t * 0.1;
    }
    if (leafGroupRef.current) {
      leafGroupRef.current.rotation.y = t * 0.15;
      leafGroupRef.current.children.forEach((child, i) => {
        child.position.y = Math.sin(t * 0.5 + i * 1.5) * 0.3 + i * 0.15;
        child.rotation.z = Math.sin(t * 0.8 + i) * 0.5;
      });
    }
  });

  return (
    <group>
      <CharacterModel
        {...props}
        primaryColor="#052e16"
        secondaryColor="#16a34a"
        emissiveColor="#4ade80"
        breathingSpeed={0.5}
        gazeInfluence={0.4}
      />
      {/* Meditation aura */}
      <mesh ref={auraRef} position={[0, 0.2, 0]}>
        <sphereGeometry args={[0.7, 16, 16]} />
        <meshStandardMaterial color="#22c55e" emissive="#4ade80" emissiveIntensity={0.5} transparent opacity={0.12} side={THREE.BackSide} />
      </mesh>
      {/* Floating leaf/code fragments */}
      <group ref={leafGroupRef}>
        {[...Array(5)].map((_, i) => (
          <mesh key={i} position={[
            Math.sin(i * 1.26) * 0.6,
            i * 0.15,
            Math.cos(i * 1.26) * 0.6
          ]}>
            <planeGeometry args={[0.06, 0.03]} />
            <meshStandardMaterial color="#4ade80" emissive="#22c55e" emissiveIntensity={1} transparent opacity={0.5} side={THREE.DoubleSide} />
          </mesh>
        ))}
      </group>
    </group>
  );
}
