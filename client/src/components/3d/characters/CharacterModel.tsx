/**
 * VisionX — CharacterModel
 * ========================================
 * Procedural 3D humanoid avatar built from Three.js primitives.
 * Supports gaze tracking, expressions, breathing, and gestures.
 * This is the BASE — archetypes customize materials and accessories.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import type { Group, Mesh } from 'three';

export interface CharacterProps {
  gazeX: number;
  gazeY: number;
  expression: string;
  idleState: string;
  gesture: string;
  primaryColor: string;
  secondaryColor: string;
  emissiveColor: string;
  breathingSpeed?: number;
  gazeInfluence?: number;
}

export function CharacterModel({
  gazeX, gazeY, expression, idleState, gesture,
  primaryColor, secondaryColor, emissiveColor,
  breathingSpeed = 1, gazeInfluence = 1,
}: CharacterProps) {
  const groupRef = useRef<Group>(null);
  const headRef = useRef<Mesh>(null);
  const leftEyeRef = useRef<Mesh>(null);
  const rightEyeRef = useRef<Mesh>(null);
  const leftPupilRef = useRef<Mesh>(null);
  const rightPupilRef = useRef<Mesh>(null);
  const bodyRef = useRef<Mesh>(null);
  const leftArmRef = useRef<Group>(null);
  const rightArmRef = useRef<Group>(null);
  const mouthRef = useRef<Mesh>(null);
  const browLeftRef = useRef<Mesh>(null);
  const browRightRef = useRef<Mesh>(null);
  const coreGlowRef = useRef<Mesh>(null);

  // Materials
  const bodyMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: primaryColor,
    emissive: emissiveColor,
    emissiveIntensity: 0.15,
    metalness: 0.6,
    roughness: 0.3,
  }), [primaryColor, emissiveColor]);

  const accentMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: secondaryColor,
    emissive: emissiveColor,
    emissiveIntensity: 0.5,
    metalness: 0.8,
    roughness: 0.2,
  }), [secondaryColor, emissiveColor]);

  const eyeWhiteMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: '#e8e8f0',
    emissive: '#ffffff',
    emissiveIntensity: 0.1,
  }), []);

  const pupilMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: emissiveColor,
    emissive: emissiveColor,
    emissiveIntensity: 0.8,
  }), [emissiveColor]);

  const mouthMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: '#1a1a2e',
    emissive: emissiveColor,
    emissiveIntensity: 0.1,
  }), [emissiveColor]);

  const glowMat = useMemo(() => new THREE.MeshStandardMaterial({
    color: emissiveColor,
    emissive: emissiveColor,
    emissiveIntensity: 1.0,
    transparent: true,
    opacity: 0.3,
  }), [emissiveColor]);

  // Animation loop
  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();

    if (!groupRef.current) return;

    // ─── Breathing ───
    const breathe = Math.sin(t * breathingSpeed) * 0.015;
    if (bodyRef.current) {
      bodyRef.current.scale.y = 1 + breathe;
      bodyRef.current.scale.x = 1 - breathe * 0.5;
    }

    // ─── Head gaze tracking ───
    if (headRef.current) {
      const targetRotY = gazeX * 0.4 * gazeInfluence;
      const targetRotX = gazeY * 0.2 * gazeInfluence;
      headRef.current.rotation.y += (targetRotY - headRef.current.rotation.y) * 0.06;
      headRef.current.rotation.x += (targetRotX - headRef.current.rotation.x) * 0.06;
    }

    // ─── Pupil tracking (tighter follow) ───
    const pupilOffsetX = gazeX * 0.04 * gazeInfluence;
    const pupilOffsetY = -gazeY * 0.03 * gazeInfluence;
    if (leftPupilRef.current) {
      leftPupilRef.current.position.x = -0.12 + pupilOffsetX;
      leftPupilRef.current.position.y = 0.05 + pupilOffsetY;
    }
    if (rightPupilRef.current) {
      rightPupilRef.current.position.x = 0.12 + pupilOffsetX;
      rightPupilRef.current.position.y = 0.05 + pupilOffsetY;
    }

    // ─── Eye expressions ───
    if (leftEyeRef.current && rightEyeRef.current) {
      let eyeScaleY = 1;
      if (expression === 'happy') eyeScaleY = 0.6;
      else if (expression === 'surprised') eyeScaleY = 1.4;
      else if (expression === 'sleeping') eyeScaleY = 0.1;
      else if (expression === 'concerned') eyeScaleY = 0.8;
      else if (expression === 'alert') eyeScaleY = 1.2;

      leftEyeRef.current.scale.y += (eyeScaleY - leftEyeRef.current.scale.y) * 0.1;
      rightEyeRef.current.scale.y += (eyeScaleY - rightEyeRef.current.scale.y) * 0.1;
    }

    // ─── Brow expressions ───
    if (browLeftRef.current && browRightRef.current) {
      let browY = 0.22;
      let browRotZ = 0;
      if (expression === 'surprised') { browY = 0.28; }
      else if (expression === 'concerned') { browY = 0.18; browRotZ = 0.2; }
      else if (expression === 'alert') { browY = 0.26; browRotZ = -0.1; }

      browLeftRef.current.position.y += (browY - browLeftRef.current.position.y) * 0.08;
      browRightRef.current.position.y += (browY - browRightRef.current.position.y) * 0.08;
      browLeftRef.current.rotation.z += (browRotZ - browLeftRef.current.rotation.z) * 0.08;
      browRightRef.current.rotation.z += (-browRotZ - browRightRef.current.rotation.z) * 0.08;
    }

    // ─── Mouth expressions ───
    if (mouthRef.current) {
      let mouthScaleX = 0.12, mouthScaleY = 0.03;
      if (expression === 'happy') { mouthScaleX = 0.15; mouthScaleY = 0.04; }
      else if (expression === 'surprised') { mouthScaleX = 0.08; mouthScaleY = 0.08; }
      else if (expression === 'alert') { mouthScaleX = 0.1; mouthScaleY = 0.02; }

      mouthRef.current.scale.x += (mouthScaleX / 0.12 - mouthRef.current.scale.x) * 0.1;
      mouthRef.current.scale.y += (mouthScaleY / 0.03 - mouthRef.current.scale.y) * 0.1;
    }

    // ─── Core glow pulse ───
    if (coreGlowRef.current) {
      const glowPulse = 0.25 + Math.sin(t * 2) * 0.08;
      (coreGlowRef.current.material as THREE.MeshStandardMaterial).opacity = glowPulse;
      coreGlowRef.current.scale.setScalar(1 + Math.sin(t * 1.5) * 0.05);
    }

    // ─── Idle animations ───
    if (idleState === 'idle') {
      // Slow look around
      if (headRef.current) {
        headRef.current.rotation.y += Math.sin(t * 0.3) * 0.002;
      }
    } else if (idleState === 'bored') {
      // Sway and look around more
      groupRef.current.rotation.z = Math.sin(t * 0.5) * 0.03;
      if (headRef.current) {
        headRef.current.rotation.y = Math.sin(t * 0.4) * 0.3;
        headRef.current.rotation.x = Math.sin(t * 0.3) * 0.1;
      }
    } else if (idleState === 'sleeping') {
      // Gentle bob
      groupRef.current.position.y = Math.sin(t * 0.5) * 0.05;
    }

    // ─── Arm gestures ───
    if (leftArmRef.current && rightArmRef.current) {
      let leftTarget = { rx: 0 , rz: 0.3 };
      let rightTarget = { rx: 0, rz: -0.3 };

      if (gesture === 'wave') {
        rightTarget = { rx: 0, rz: -1.2 + Math.sin(t * 6) * 0.3 };
      } else if (gesture === 'point') {
        rightTarget = { rx: -0.5, rz: -1.0 };
      } else if (gesture === 'thumbsUp') {
        rightTarget = { rx: -0.3, rz: -1.0 };
      } else if (gesture === 'alert') {
        leftTarget = { rx: -0.3, rz: 0.8 };
        rightTarget = { rx: -0.3, rz: -0.8 };
      } else if (gesture === 'thinking') {
        rightTarget = { rx: -0.8, rz: -0.5 };
      }

      // Subtle idle arm sway
      if (gesture === 'none') {
        leftTarget.rz += Math.sin(t * 0.8) * 0.05;
        rightTarget.rz += Math.sin(t * 0.8 + 1) * 0.05;
      }

      leftArmRef.current.rotation.x += (leftTarget.rx - leftArmRef.current.rotation.x) * 0.06;
      leftArmRef.current.rotation.z += (leftTarget.rz - leftArmRef.current.rotation.z) * 0.06;
      rightArmRef.current.rotation.x += (rightTarget.rx - rightArmRef.current.rotation.x) * 0.06;
      rightArmRef.current.rotation.z += (rightTarget.rz - rightArmRef.current.rotation.z) * 0.06;
    }

    // ─── Floating bob ───
    groupRef.current.position.y += (Math.sin(t * 0.8) * 0.08 - groupRef.current.position.y) * 0.02;
  });

  return (
    <group ref={groupRef}>
      {/* ─── Head ─── */}
      <group ref={headRef} position={[0, 0.85, 0]}>
        {/* Skull */}
        <mesh>
          <sphereGeometry args={[0.28, 24, 24]} />
          <primitive object={bodyMat} attach="material" />
        </mesh>

        {/* Face plate / visor accent */}
        <mesh position={[0, 0, 0.22]} rotation={[0, 0, 0]}>
          <planeGeometry args={[0.4, 0.2]} />
          <primitive object={accentMat} attach="material" />
        </mesh>

        {/* Left Eye */}
        <mesh ref={leftEyeRef} position={[-0.12, 0.05, 0.24]}>
          <sphereGeometry args={[0.055, 16, 16]} />
          <primitive object={eyeWhiteMat} attach="material" />
        </mesh>

        {/* Right Eye */}
        <mesh ref={rightEyeRef} position={[0.12, 0.05, 0.24]}>
          <sphereGeometry args={[0.055, 16, 16]} />
          <primitive object={eyeWhiteMat} attach="material" />
        </mesh>

        {/* Left Pupil */}
        <mesh ref={leftPupilRef} position={[-0.12, 0.05, 0.29]}>
          <sphereGeometry args={[0.025, 12, 12]} />
          <primitive object={pupilMat} attach="material" />
        </mesh>

        {/* Right Pupil */}
        <mesh ref={rightPupilRef} position={[0.12, 0.05, 0.29]}>
          <sphereGeometry args={[0.025, 12, 12]} />
          <primitive object={pupilMat} attach="material" />
        </mesh>

        {/* Left Brow */}
        <mesh ref={browLeftRef} position={[-0.12, 0.22, 0.25]}>
          <boxGeometry args={[0.08, 0.015, 0.01]} />
          <primitive object={accentMat} attach="material" />
        </mesh>

        {/* Right Brow */}
        <mesh ref={browRightRef} position={[0.12, 0.22, 0.25]}>
          <boxGeometry args={[0.08, 0.015, 0.01]} />
          <primitive object={accentMat} attach="material" />
        </mesh>

        {/* Mouth */}
        <mesh ref={mouthRef} position={[0, -0.1, 0.26]}>
          <planeGeometry args={[0.12, 0.03]} />
          <primitive object={mouthMat} attach="material" />
        </mesh>
      </group>

      {/* ─── Neck ─── */}
      <mesh position={[0, 0.55, 0]}>
        <cylinderGeometry args={[0.06, 0.08, 0.12, 12]} />
        <primitive object={bodyMat} attach="material" />
      </mesh>

      {/* ─── Body / Torso ─── */}
      <mesh ref={bodyRef} position={[0, 0.15, 0]}>
        <capsuleGeometry args={[0.22, 0.4, 8, 16]} />
        <primitive object={bodyMat} attach="material" />
      </mesh>

      {/* ─── Core Glow (chest) ─── */}
      <mesh ref={coreGlowRef} position={[0, 0.25, 0.18]}>
        <sphereGeometry args={[0.06, 12, 12]} />
        <primitive object={glowMat} attach="material" />
      </mesh>

      {/* ─── Shoulder Guards ─── */}
      <mesh position={[-0.3, 0.4, 0]}>
        <sphereGeometry args={[0.07, 12, 12]} />
        <primitive object={accentMat} attach="material" />
      </mesh>
      <mesh position={[0.3, 0.4, 0]}>
        <sphereGeometry args={[0.07, 12, 12]} />
        <primitive object={accentMat} attach="material" />
      </mesh>

      {/* ─── Left Arm ─── */}
      <group ref={leftArmRef} position={[-0.32, 0.35, 0]} rotation={[0, 0, 0.3]}>
        <mesh position={[0, -0.2, 0]}>
          <capsuleGeometry args={[0.04, 0.3, 6, 12]} />
          <primitive object={bodyMat} attach="material" />
        </mesh>
        {/* Hand */}
        <mesh position={[0, -0.42, 0]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <primitive object={accentMat} attach="material" />
        </mesh>
      </group>

      {/* ─── Right Arm ─── */}
      <group ref={rightArmRef} position={[0.32, 0.35, 0]} rotation={[0, 0, -0.3]}>
        <mesh position={[0, -0.2, 0]}>
          <capsuleGeometry args={[0.04, 0.3, 6, 12]} />
          <primitive object={bodyMat} attach="material" />
        </mesh>
        {/* Hand */}
        <mesh position={[0, -0.42, 0]}>
          <sphereGeometry args={[0.05, 8, 8]} />
          <primitive object={accentMat} attach="material" />
        </mesh>
      </group>

      {/* ─── Lower Body ─── */}
      <mesh position={[0, -0.25, 0]}>
        <coneGeometry args={[0.22, 0.4, 8]} />
        <primitive object={bodyMat} attach="material" />
      </mesh>
    </group>
  );
}
