/**
 * VisionX — Heatmap Component
 * Spatial activity density visualization
 */

import { useMemo } from 'react';

interface HeatmapCell {
  x: number; y: number; value: number;
}

interface HeatmapProps {
  data: HeatmapCell[];
  width?: number;
  height?: number;
  gridSize?: number;
  title?: string;
}

function valueToColor(value: number, max: number): string {
  const ratio = Math.min(value / max, 1);
  if (ratio < 0.25) return `rgba(56,189,248,${ratio * 2})`;
  if (ratio < 0.5) return `rgba(34,197,94,${ratio * 1.5})`;
  if (ratio < 0.75) return `rgba(251,191,36,${ratio * 1.2})`;
  return `rgba(248,113,113,${Math.max(ratio, 0.6)})`;
}

export function Heatmap({ data, width = 400, height = 300, gridSize = 20, title }: HeatmapProps) {
  const maxValue = useMemo(() => Math.max(...data.map((d) => d.value), 1), [data]);
  const cols = Math.floor(width / gridSize);
  const rows = Math.floor(height / gridSize);

  // If no data, generate placeholder
  const cells = useMemo(() => {
    if (data.length > 0) return data;
    return Array.from({ length: cols * rows }, (_, i) => ({
      x: (i % cols) * gridSize,
      y: Math.floor(i / cols) * gridSize,
      value: Math.random() * maxValue,
    }));
  }, [data, cols, rows, gridSize, maxValue]);

  return (
    <div>
      {title && <h3 className="font-semibold" style={{ marginBottom: 12 }}>{title}</h3>}
      <div style={{
        position: 'relative', width, height,
        background: 'rgba(0,0,0,0.3)', borderRadius: 'var(--radius-sm)', overflow: 'hidden',
      }}>
        {cells.map((cell, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: cell.x, top: cell.y,
              width: gridSize - 1, height: gridSize - 1,
              background: valueToColor(cell.value, maxValue),
              borderRadius: 2,
              transition: 'background 0.3s',
            }}
          />
        ))}
        {/* Zone labels */}
        <div style={{
          position: 'absolute', bottom: 8, right: 8, fontSize: '0.6rem',
          color: 'rgba(255,255,255,0.4)', fontFamily: 'var(--font-mono)',
        }}>
          Heat density map
        </div>
      </div>
    </div>
  );
}
