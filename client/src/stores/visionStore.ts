/**
 * VisionX — Vision Store
 * Real-time detection state from edge/cloud AI pipeline
 */

import { create } from 'zustand';

interface Detection {
  id: string;
  class: string;
  confidence: number;
  bbox: [number, number, number, number]; // x, y, w, h
  trackId?: number;
}

interface VisionState {
  detections: Detection[];
  fps: number;
  latency: number;
  isProcessing: boolean;
  frameCount: number;
  setDetections: (detections: Detection[]) => void;
  setFps: (fps: number) => void;
  setLatency: (latency: number) => void;
  setProcessing: (isProcessing: boolean) => void;
  incrementFrame: () => void;
  reset: () => void;
}

export const useVisionStore = create<VisionState>((set) => ({
  detections: [],
  fps: 0,
  latency: 0,
  isProcessing: false,
  frameCount: 0,

  setDetections: (detections) => set({ detections }),
  setFps: (fps) => set({ fps }),
  setLatency: (latency) => set({ latency }),
  setProcessing: (isProcessing) => set({ isProcessing }),
  incrementFrame: () => set((s) => ({ frameCount: s.frameCount + 1 })),
  reset: () => set({ detections: [], fps: 0, latency: 0, isProcessing: false, frameCount: 0 }),
}));
