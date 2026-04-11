/**
 * VisionX — 3D Scene Container
 * React Three Fiber canvas with environment and lighting
 */

import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Stars } from '@react-three/drei';
import { Suspense } from 'react';
import { FloatingObjects } from './FloatingObjects';
import { AnimatedBackground } from './Background';

interface SceneProps {
  theme?: string;
  interactive?: boolean;
}

export function Scene({ theme = 'obsidian', interactive = false }: SceneProps) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: -1,
      pointerEvents: interactive ? 'auto' : 'none',
    }}>
      <Canvas
        camera={{ position: [0, 0, 8], fov: 45 }}
        dpr={[1, 1.5]}
        style={{ background: 'transparent' }}
      >
        <Suspense fallback={null}>
          {/* Lighting */}
          <ambientLight intensity={0.15} />
          <pointLight position={[10, 10, 10]} intensity={0.4} color="#a78bfa" />
          <pointLight position={[-10, -5, 5]} intensity={0.2} color="#38bdf8" />

          {/* Background effects */}
          <AnimatedBackground theme={theme} />
          <FloatingObjects count={20} theme={theme} />

          {/* Stars */}
          <Stars
            radius={50}
            depth={60}
            count={1500}
            factor={3}
            saturation={0.3}
            fade
            speed={0.5}
          />

          {/* Environment */}
          <Environment preset="night" />

          {interactive && <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.3} />}
        </Suspense>
      </Canvas>
    </div>
  );
}
