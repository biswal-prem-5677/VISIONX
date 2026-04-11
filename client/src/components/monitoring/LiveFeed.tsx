/**
 * VisionX — LiveFeed Component
 * Real-time camera feed display with WebSocket video stream
 */

import { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface LiveFeedProps {
  cameraName?: string;
  streamUrl?: string;
  onPause?: () => void;
  onResume?: () => void;
}

export function LiveFeed({ 
  cameraName = 'Camera_01 — Main Entrance',
  streamUrl,
}: LiveFeedProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [resolution] = useState('1280×720');
  const [mode] = useState('Balanced');

  // When streamUrl is available, connect to WebSocket video
  useEffect(() => {
    if (!streamUrl || !canvasRef.current) return;
    // Future: WebSocket frame rendering here
  }, [streamUrl]);

  return (
    <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Feed Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '12px 16px', borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)' }} />
          <span className="font-medium text-sm">{cameraName}</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-accent" style={{ fontSize: '0.65rem' }}>30 FPS</span>
          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>12ms</span>
        </div>
      </div>

      {/* Video Area */}
      <div style={{
        position: 'relative', width: '100%', aspectRatio: '16/9',
        background: 'rgba(0,0,0,0.4)', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: streamUrl ? 'block' : 'none' }} />
        {!streamUrl && (
          <div style={{ textAlign: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>📹</div>
            <p className="text-sm">Live camera feed will render here</p>
            <p className="text-xs" style={{ opacity: 0.5 }}>WebSocket → Canvas → BoundingBox overlay</p>
          </div>
        )}
      </div>

      {/* Controls */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '10px 16px', borderTop: '1px solid var(--border)',
      }}>
        <motion.button
          className="glow-btn glow-btn--primary glow-btn--sm"
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsPaused(!isPaused)}
        >
          {isPaused ? '▶ Resume' : '⏸ Pause'}
        </motion.button>
        <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
          Resolution: {resolution} | Mode: {mode}
        </span>
      </div>
    </div>
  );
}
