/**
 * VisionX — Analytics Page (MODE 2: Analytics Dashboard)
 * Charts, heatmaps, event history, object counts over time
 */

import { motion } from 'framer-motion';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer,
} from 'recharts';
import { GlassCard } from '../components/ui/GlassCard';

const hourlyData = [
  { hour: '00', persons: 3, vehicles: 1 },
  { hour: '02', persons: 1, vehicles: 0 },
  { hour: '04', persons: 2, vehicles: 1 },
  { hour: '06', persons: 12, vehicles: 8 },
  { hour: '08', persons: 45, vehicles: 22 },
  { hour: '10', persons: 38, vehicles: 15 },
  { hour: '12', persons: 52, vehicles: 18 },
  { hour: '14', persons: 41, vehicles: 20 },
  { hour: '16', persons: 55, vehicles: 25 },
  { hour: '18', persons: 48, vehicles: 30 },
  { hour: '20', persons: 25, vehicles: 12 },
  { hour: '22', persons: 8, vehicles: 4 },
];

const eventBreakdown = [
  { name: 'Person', value: 340, color: '#a78bfa' },
  { name: 'Vehicle', value: 156, color: '#38bdf8' },
  { name: 'Bicycle', value: 42, color: '#22c55e' },
  { name: 'Animal', value: 12, color: '#fb923c' },
];

const weeklyEvents = [
  { day: 'Mon', events: 67 },
  { day: 'Tue', events: 82 },
  { day: 'Wed', events: 91 },
  { day: 'Thu', events: 73 },
  { day: 'Fri', events: 110 },
  { day: 'Sat', events: 45 },
  { day: 'Sun', events: 38 },
];

const recentEvents = [
  { id: 1, type: 'Intrusion', camera: 'Camera_01', time: '14:32:05', severity: 'danger' },
  { id: 2, type: 'Crowd Alert', camera: 'Camera_02', time: '14:28:11', severity: 'warning' },
  { id: 3, type: 'Vehicle Parked', camera: 'Camera_03', time: '14:15:44', severity: 'info' },
  { id: 4, type: 'Person Running', camera: 'Camera_01', time: '14:02:22', severity: 'warning' },
  { id: 5, type: 'Object Left', camera: 'Camera_02', time: '13:55:08', severity: 'danger' },
];

const summaryStats = [
  { label: 'Total Detections', value: '2,847', change: '+12%', positive: true },
  { label: 'Events Triggered', value: '156', change: '+8%', positive: true },
  { label: 'Avg Processing', value: '14ms', change: '-3ms', positive: true },
  { label: 'Accuracy', value: '94.2%', change: '+0.5%', positive: true },
];

export default function Analytics() {
  return (
    <div className="analytics">
      {/* Summary Stats */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        {summaryStats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <GlassCard className="stat-card">
              <div className="stat-card__info" style={{ width: '100%' }}>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{stat.label}</span>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span className="text-2xl font-bold">{stat.value}</span>
                  <span className="badge badge-success text-xs">{stat.change}</span>
                </div>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Hourly Activity */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Hourly Activity</h3>
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={hourlyData}>
                <defs>
                  <linearGradient id="personGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="vehicleGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="hour" stroke="var(--text-tertiary)" fontSize={12} />
                <YAxis stroke="var(--text-tertiary)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                    borderRadius: 8, color: 'var(--text-primary)', fontSize: 12,
                  }}
                />
                <Area type="monotone" dataKey="persons" stroke="var(--accent)" fill="url(#personGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="vehicles" stroke="#38bdf8" fill="url(#vehicleGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>

        {/* Detection Breakdown */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.35 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Detection Breakdown</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
              <ResponsiveContainer width="50%" height={220}>
                <PieChart>
                  <Pie data={eventBreakdown} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                    paddingAngle={4} dataKey="value" stroke="none">
                    {eventBreakdown.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {eventBreakdown.map((item) => (
                  <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{
                      width: 10, height: 10, borderRadius: '50%', background: item.color,
                    }} />
                    <span className="text-sm">{item.name}</span>
                    <span className="text-sm font-bold mono" style={{ marginLeft: 'auto' }}>{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Weekly Events */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Weekly Events</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyEvents}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="day" stroke="var(--text-tertiary)" fontSize={12} />
                <YAxis stroke="var(--text-tertiary)" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                    borderRadius: 8, color: 'var(--text-primary)', fontSize: 12,
                  }}
                />
                <Bar dataKey="events" fill="var(--accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </motion.div>

        {/* Recent Events Table */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45 }}>
          <GlassCard>
            <h3 className="font-semibold" style={{ marginBottom: 16 }}>Recent Events</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentEvents.map((e) => (
                <div key={e.id} className="glass-subtle" style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 14px', borderRadius: 'var(--radius-sm)',
                }}>
                  <div>
                    <span className={`badge badge-${e.severity}`} style={{ marginRight: 10 }}>
                      {e.severity === 'danger' ? '🔴' : e.severity === 'warning' ? '🟡' : '🔵'}
                    </span>
                    <span className="font-medium text-sm">{e.type}</span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{e.camera}</span>
                    <span className="text-xs mono" style={{ color: 'var(--text-tertiary)', marginLeft: 12 }}>{e.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </div>
  );
}
