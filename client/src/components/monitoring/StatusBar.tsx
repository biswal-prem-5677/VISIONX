/**
 * VisionX — StatusBar Component
 * FPS, latency, connection status display
 */

interface StatusBarProps {
  fps: number;
  latency: number;
  isConnected: boolean;
  mode: string;
  resolution: string;
}

export function StatusBar({ fps, latency, isConnected, mode, resolution }: StatusBarProps) {
  return (
    <div style={{
      display: 'flex', gap: 16, alignItems: 'center', padding: '8px 14px',
      background: 'var(--surface)', borderRadius: 'var(--radius-sm)',
      fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          background: isConnected ? 'var(--success)' : 'var(--danger)',
        }} />
        <span style={{ color: isConnected ? 'var(--success)' : 'var(--danger)' }}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      <span style={{ color: fps > 20 ? 'var(--success)' : 'var(--warning)' }}>
        {fps} FPS
      </span>
      <span style={{ color: latency < 20 ? 'var(--success)' : latency < 50 ? 'var(--warning)' : 'var(--danger)' }}>
        {latency}ms
      </span>
      <span style={{ color: 'var(--text-tertiary)' }}>{resolution}</span>
      <span style={{ color: 'var(--text-tertiary)' }}>Mode: {mode}</span>
    </div>
  );
}
