/**
 * VisionX — DeviceManager Component
 * Camera/device management panel
 */

import { GlowButton } from '../ui/GlowButton';

interface Device {
  id: number;
  name: string;
  location: string;
  type: 'webcam' | 'rtsp' | 'ip' | 'file';
  status: 'online' | 'offline' | 'error';
  resolution: string;
  fps: number;
}

interface DeviceManagerProps {
  devices: Device[];
  onAdd?: () => void;
  onRemove?: (id: number) => void;
  onRestart?: (id: number) => void;
}

const STATUS_COLORS = { online: 'var(--success)', offline: 'var(--text-tertiary)', error: 'var(--danger)' };
const TYPE_ICONS = { webcam: '📹', rtsp: '🌐', ip: '📡', file: '🎬' };

export function DeviceManager({ devices, onAdd, onRemove, onRestart }: DeviceManagerProps) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h3 className="font-semibold">Camera Sources</h3>
        <GlowButton size="sm" onClick={onAdd}>+ Add Camera</GlowButton>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {devices.map((d) => (
          <div key={d.id} className="glass-subtle" style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '14px 16px', borderRadius: 'var(--radius-sm)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 18 }}>{TYPE_ICONS[d.type]}</span>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: STATUS_COLORS[d.status],
                  }} />
                  <span className="font-medium text-sm">{d.name}</span>
                </div>
                <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                  {d.location} · {d.resolution} · {d.fps} FPS
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              {d.status === 'error' && (
                <GlowButton variant="secondary" size="sm" onClick={() => onRestart?.(d.id)}>
                  Restart
                </GlowButton>
              )}
              <GlowButton variant="ghost" size="sm" onClick={() => onRemove?.(d.id)}>
                ✕
              </GlowButton>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
