/**
 * VisionX — Guardian Archetype (Obsidian Theme)
 * Stoic, dark armor, glowing purple eyes, floating shield fragments.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Mesh, Group } from 'three';
import { CharacterModel, type CharacterProps } from '../CharacterModel';

interface GuardianProps extends Omit<CharacterProps, 'primaryColor' | 'secondaryColor' | 'emissiveColor'> {}

export function Guardian(props: GuardianProps) {
  const shieldRef1 = useRef<Mesh>(null);
  const shieldRef2 = useRef<Mesh>(null);
  const shieldRef3 = useRef<Mesh>(null);
  const orbitGroupRef = useRef<Group>(null);

  const shieldMat = new THREE.MeshStandardMaterial({
    color: '#2d1b69',
    emissive: '#a78bfa',
    emissiveIntensity: 0.4,
    transparent: true,
    opacity: 0.6,
    metalness: 0.9,
    roughness: 0.1,
    side: THREE.DoubleSide,
  });

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (orbitGroupRef.current) {
      orbitGroupRef.current.rotation.y = t * 0.3;
    }
    [shieldRef1, shieldRef2, shieldRef3].forEach((ref, i) => {
      if (ref.current) {
        ref.current.position.y = Math.sin(t * 0.8 + i * 2.1) * 0.15;
        ref.current.rotation.z = Math.sin(t * 0.5 + i) * 0.2;
        (ref.current.material as THREE.MeshStandardMaterial).opacity =
          0.4 + Math.sin(t * 1.5 + i * 1.3) * 0.2;
      }
    });
  });

  return (
    <group>
      <CharacterModel
        {...props}
        primaryColor="#1a1030"
        secondaryColor="#6d28d9"
        emissiveColor="#a78bfa"
        breathingSpeed={0.7}
        gazeInfluence={0.6}
      />
      {/* Floating shield fragments */}
      <group ref={orbitGroupRef}>
        <mesh ref={shieldRef1} position={[-0.6, 0.2, 0.3]}>
          <boxGeometry args={[0.15, 0.25, 0.02]} />
          <primitive object={shieldMat} attach="material" />
        </mesh>
        <mesh ref={shieldRef2} position={[0.5, 0.5, -0.2]}>
          <boxGeometry args={[0.12, 0.2, 0.02]} />
          <primitive object={shieldMat} attach="material" />
        </mesh>
        <mesh ref={shieldRef3} position={[0.1, -0.1, 0.5]}>
          <boxGeometry args={[0.18, 0.12, 0.02]} />
          <primitive object={shieldMat} attach="material" />
        </mesh>
      </group>
    </group>
  );
}
