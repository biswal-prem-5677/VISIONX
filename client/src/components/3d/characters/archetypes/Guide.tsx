/**
 * VisionX — Guide Archetype (Aurora Theme)
 * Airy, energetic, blue-white glow, floating light orbs around hands.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Mesh, Group } from 'three';
import { CharacterModel, type CharacterProps } from '../CharacterModel';

interface GuideProps extends Omit<CharacterProps, 'primaryColor' | 'secondaryColor' | 'emissiveColor'> {}

export function Guide(props: GuideProps) {
  const orbsRef = useRef<Group>(null);
  const orb1Ref = useRef<Mesh>(null);
  const orb2Ref = useRef<Mesh>(null);
  const haloRef = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (orbsRef.current) orbsRef.current.rotation.y = t * 0.5;
    if (orb1Ref.current) {
      orb1Ref.current.position.set(
        Math.sin(t * 1.2) * 0.5,
        0.1 + Math.cos(t * 0.8) * 0.3,
        Math.cos(t * 1.2) * 0.5
      );
      orb1Ref.current.scale.setScalar(0.8 + Math.sin(t * 2) * 0.2);
    }
    if (orb2Ref.current) {
      orb2Ref.current.position.set(
        Math.sin(t * 1.2 + Math.PI) * 0.5,
        0.2 + Math.cos(t * 0.8 + Math.PI) * 0.3,
        Math.cos(t * 1.2 + Math.PI) * 0.5
      );
      orb2Ref.current.scale.setScalar(0.7 + Math.sin(t * 2 + 1) * 0.2);
    }
    if (haloRef.current) {
      haloRef.current.rotation.z = t * 0.4;
      (haloRef.current.material as THREE.MeshStandardMaterial).opacity =
        0.2 + Math.sin(t * 1.5) * 0.1;
    }
  });

  return (
    <group>
      <CharacterModel
        {...props}
        primaryColor="#0c2d48"
        secondaryColor="#0ea5e9"
        emissiveColor="#38bdf8"
        breathingSpeed={1.2}
        gazeInfluence={1.2}
      />
      {/* Floating light orbs */}
      <group ref={orbsRef}>
        <mesh ref={orb1Ref}>
          <sphereGeometry args={[0.06, 12, 12]} />
          <meshStandardMaterial color="#7dd3fc" emissive="#38bdf8" emissiveIntensity={1.5} transparent opacity={0.7} />
        </mesh>
        <mesh ref={orb2Ref}>
          <sphereGeometry args={[0.05, 12, 12]} />
          <meshStandardMaterial color="#bae6fd" emissive="#38bdf8" emissiveIntensity={1.2} transparent opacity={0.6} />
        </mesh>
      </group>
      {/* Halo ring */}
      <mesh ref={haloRef} position={[0, 1.2, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.2, 0.015, 8, 32]} />
        <meshStandardMaterial color="#38bdf8" emissive="#38bdf8" emissiveIntensity={0.8} transparent opacity={0.3} />
      </mesh>
    </group>
  );
}
