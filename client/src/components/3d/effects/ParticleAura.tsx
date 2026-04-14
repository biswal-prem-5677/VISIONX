/**
 * VisionX — ParticleAura Effect
 * ========================================
 * Theme-colored particle system around the character.
 * Each archetype has unique particle behavior.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface ParticleAuraProps {
  color: string;
  count?: number;
  radius?: number;
  speed?: number;
  archetype?: string;
}

export function ParticleAura({
  color, count = 40, radius = 0.8, speed = 1, archetype = 'guardian',
}: ParticleAuraProps) {
  const pointsRef = useRef<THREE.Points>(null);

  const { positions, velocities, sizes } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);
    const sz = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const r = radius * (0.5 + Math.random() * 0.5);

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.cos(phi);
      pos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);

      vel[i * 3] = (Math.random() - 0.5) * 0.01;
      vel[i * 3 + 1] = (Math.random() - 0.5) * 0.01;
      vel[i * 3 + 2] = (Math.random() - 0.5) * 0.01;

      sz[i] = 0.02 + Math.random() * 0.04;
    }
    return { positions: pos, velocities: vel, sizes: sz };
  }, [count, radius]);

  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    return geo;
  }, [positions, sizes]);

  useFrame(({ clock }) => {
    if (!pointsRef.current) return;
    const t = clock.getElapsedTime() * speed;
    const posAttr = pointsRef.current.geometry.attributes.position;
    const posArray = posAttr.array as Float32Array;

    for (let i = 0; i < count; i++) {
      const idx = i * 3;

      if (archetype === 'guardian') {
        // Slow orbit
        const angle = t * 0.3 + i * 0.15;
        const r = radius * (0.6 + Math.sin(t * 0.5 + i) * 0.2);
        posArray[idx] = r * Math.cos(angle);
        posArray[idx + 1] = Math.sin(t * 0.4 + i * 0.3) * 0.4;
        posArray[idx + 2] = r * Math.sin(angle);
      } else if (archetype === 'guide') {
        // Sparkle upward
        posArray[idx] += velocities[idx];
        posArray[idx + 1] += 0.005 + Math.random() * 0.003;
        posArray[idx + 2] += velocities[idx + 2];
        if (posArray[idx + 1] > 1.5) {
          posArray[idx] = (Math.random() - 0.5) * radius;
          posArray[idx + 1] = -0.5;
          posArray[idx + 2] = (Math.random() - 0.5) * radius;
        }
      } else if (archetype === 'muse') {
        // Fast spiral
        const angle = t * 1.2 + i * 0.13;
        const r2 = radius * (0.4 + Math.sin(t + i) * 0.3);
        posArray[idx] = r2 * Math.cos(angle);
        posArray[idx + 1] = Math.sin(t * 0.8 + i * 0.5) * 0.6;
        posArray[idx + 2] = r2 * Math.sin(angle);
      } else if (archetype === 'sage') {
        // Gentle float
        posArray[idx] += Math.sin(t * 0.3 + i) * 0.001;
        posArray[idx + 1] += Math.cos(t * 0.2 + i * 0.7) * 0.001;
        posArray[idx + 2] += Math.sin(t * 0.25 + i * 1.1) * 0.001;
      } else if (archetype === 'pilot') {
        // Ember sparks
        posArray[idx] += velocities[idx] * 2;
        posArray[idx + 1] -= 0.008 + Math.random() * 0.005;
        posArray[idx + 2] += velocities[idx + 2] * 2;
        if (posArray[idx + 1] < -1) {
          posArray[idx] = (Math.random() - 0.5) * 0.5;
          posArray[idx + 1] = 0.5 + Math.random() * 0.5;
          posArray[idx + 2] = (Math.random() - 0.5) * 0.5;
        }
      }
    }
    posAttr.needsUpdate = true;
    pointsRef.current.rotation.y += 0.001;
  });

  return (
    <points ref={pointsRef} geometry={geometry}>
      <pointsMaterial
        color={color}
        size={0.04}
        transparent
        opacity={0.6}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
        sizeAttenuation
      />
    </points>
  );
}
