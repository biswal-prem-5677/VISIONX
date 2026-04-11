/**
 * VisionX — App Constants
 */

export const APP_NAME = 'VisionX';
export const APP_VERSION = '1.0.0';
export const APP_TAGLINE = 'Jarvis for Vision';

// WebSocket
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/live';

// API
export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Performance modes
export const PERFORMANCE_MODES = [
  { id: 'lite', label: 'Lite', desc: 'Low power, mobile-friendly', resolution: 320, fps: 15 },
  { id: 'balanced', label: 'Balanced', desc: 'General purpose', resolution: 640, fps: 30 },
  { id: 'max', label: 'Max', desc: 'Full power, GPU required', resolution: 1280, fps: 60 },
] as const;

// Detection classes
export const DETECTION_CLASSES = [
  'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck',
  'traffic light', 'stop sign', 'cat', 'dog', 'backpack',
  'umbrella', 'handbag', 'suitcase', 'bottle', 'cup',
  'chair', 'couch', 'laptop', 'cell phone', 'book',
] as const;

// Severity colors
export const SEVERITY_COLORS = {
  info: '#38bdf8',
  warning: '#fbbf24',
  danger: '#f87171',
  success: '#22c55e',
} as const;

// Timing
export const STATE_SAVE_INTERVAL = 5000;
export const WS_RECONNECT_INTERVAL = 3000;
export const WS_MAX_RETRIES = 10;
