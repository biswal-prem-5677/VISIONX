/**
 * VisionX — Muse Archetype (Cyber Theme)
 * Ethereal, holographic body, cyan data streams, follows cursor closely.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';

import type { Mesh, Group } from 'three';
import { CharacterModel, type CharacterProps } from '../CharacterModel';

interface MuseProps extends Omit<CharacterProps, 'primaryColor' | 'secondaryColor' | 'emissiveColor'> {}

export function Muse(props: MuseProps) {
  const dataStreamsRef = useRef<Group>(null);
  const ring1Ref = useRef<Mesh>(null);
  const ring2Ref = useRef<Mesh>(null);
  const ring3Ref = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (dataStreamsRef.current) {
      dataStreamsRef.current.rotation.y = t * 0.8;
    }
    [ring1Ref, ring2Ref, ring3Ref].forEach((ref, i) => {
      if (ref.current) {
        ref.current.rotation.x = t * (0.5 + i * 0.2);
        ref.current.rotation.z = t * (0.3 + i * 0.15);
        const scale = 1 + Math.sin(t * 1.5 + i * 2) * 0.1;
        ref.current.scale.setScalar(scale);
      }
    });
  });

  return (
    <group>
      <CharacterModel
        {...props}
        primaryColor="#0a1929"
        secondaryColor="#06b6d4"
        emissiveColor="#22d3ee"
        breathingSpeed={1.5}
        gazeInfluence={1.5}
      />
      {/* Holographic data rings */}
      <group ref={dataStreamsRef}>
        <mesh ref={ring1Ref} position={[0, 0.3, 0]}>
          <torusGeometry args={[0.45, 0.008, 6, 48]} />
          <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={1} transparent opacity={0.35} />
        </mesh>
        <mesh ref={ring2Ref} position={[0, 0.1, 0]}>
          <torusGeometry args={[0.55, 0.006, 6, 48]} />
          <meshStandardMaterial color="#67e8f9" emissive="#06b6d4" emissiveIntensity={0.8} transparent opacity={0.25} />
        </mesh>
        <mesh ref={ring3Ref} position={[0, 0.5, 0]}>
          <torusGeometry args={[0.35, 0.01, 6, 48]} />
          <meshStandardMaterial color="#a5f3fc" emissive="#22d3ee" emissiveIntensity={0.6} transparent opacity={0.2} />
        </mesh>
      </group>
    </group>
  );
}
