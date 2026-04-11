/**
 * VisionX — BoundingBoxes Component
 * Detection overlay renderer for camera feed
 */

import { useMemo } from 'react';

interface Detection {
  id: number;
  label: string;
  confidence: number;
  x: number; y: number; w: number; h: number;
  color?: string;
}

interface BoundingBoxesProps {
  detections: Detection[];
  width: number;
  height: number;
}

const DEFAULT_COLORS: Record<string, string> = {
  Person: '#a78bfa', Car: '#38bdf8', Bicycle: '#22c55e',
  Truck: '#fb923c', Dog: '#f472b6', default: '#8b5cf6',
};

export function BoundingBoxes({ detections, width, height }: BoundingBoxesProps) {
  const boxes = useMemo(() => detections.map((d) => ({
    ...d,
    color: d.color || DEFAULT_COLORS[d.label] || DEFAULT_COLORS.default,
  })), [detections]);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
    >
      {boxes.map((d) => (
        <g key={d.id}>
          {/* Box */}
          <rect
            x={d.x} y={d.y} width={d.w} height={d.h}
            fill="none" stroke={d.color} strokeWidth={2}
            rx={4} ry={4}
          />
          {/* Label background */}
          <rect
            x={d.x} y={d.y - 22} width={d.label.length * 8 + 50} height={20}
            fill={d.color} rx={4} ry={4} opacity={0.9}
          />
          {/* Label text */}
          <text
            x={d.x + 6} y={d.y - 7}
            fill="#fff" fontSize={11} fontWeight={600}
            fontFamily="var(--font-mono)"
          >
            ID:{d.id} | {d.label} {Math.round(d.confidence * 100)}%
          </text>
        </g>
      ))}
    </svg>
  );
}
