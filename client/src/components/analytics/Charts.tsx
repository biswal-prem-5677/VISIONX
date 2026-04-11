/**
 * VisionX — Charts Component
 * Time-series graphs for analytics
 */

import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';

interface ChartDataPoint {
  label: string;
  [key: string]: string | number;
}

interface ChartsProps {
  data: ChartDataPoint[];
  title: string;
  dataKeys: { key: string; color: string; gradientId: string }[];
  height?: number;
}

export function Charts({ data, title, dataKeys, height = 260 }: ChartsProps) {
  return (
    <div>
      <h3 className="font-semibold" style={{ marginBottom: 16 }}>{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            {dataKeys.map((dk) => (
              <linearGradient key={dk.gradientId} id={dk.gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={dk.color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={dk.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="label" stroke="var(--text-tertiary)" fontSize={12} />
          <YAxis stroke="var(--text-tertiary)" fontSize={12} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-secondary)', border: '1px solid var(--border)',
              borderRadius: 8, color: 'var(--text-primary)', fontSize: 12,
            }}
          />
          {dataKeys.map((dk) => (
            <Area
              key={dk.key}
              type="monotone"
              dataKey={dk.key}
              stroke={dk.color}
              fill={`url(#${dk.gradientId})`}
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
