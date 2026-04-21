/**
 * VisionX — Vision WebSocket Hook
 * Bridges the backend WebSocket stream to Zustand stores.
 * Handles: detection frames, events, system status.
 */

import { useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import { useVisionStore } from '../stores/visionStore';
import { useEventStore } from '../stores/eventStore';
import { useOfflineStore } from '../stores/offlineStore';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/vision`;

export function useVisionStream(url?: string) {
  const setDetections = useVisionStore((s) => s.setDetections);
  const setFps = useVisionStore((s) => s.setFps);
  const setLatency = useVisionStore((s) => s.setLatency);
  const setProcessing = useVisionStore((s) => s.setProcessing);
  const incrementFrame = useVisionStore((s) => s.incrementFrame);
  const addEvent = useEventStore((s) => s.addEvent);
  const setOnline = useOfflineStore((s) => s.setOnline);

  const handleMessage = useCallback(
    (data: any) => {
      if (!data || typeof data !== 'object') return;

      switch (data.type) {
        case 'frame':
        case 'detection': {
          // Pipeline frame result
          if (Array.isArray(data.detections)) {
            setDetections(
              data.detections.map((d: any, i: number) => ({
                id: d.id || `det-${Date.now()}-${i}`,
                class: d.class_name || d.class || 'unknown',
                confidence: d.confidence || 0,
                bbox: d.bbox
                  ? [d.bbox.x1 || 0, d.bbox.y1 || 0, d.bbox.x2 || 0, d.bbox.y2 || 0]
                  : [0, 0, 0, 0],
                trackId: d.track_id || d.trackId,
              }))
            );
          }
          if (typeof data.fps === 'number') setFps(data.fps);
          if (typeof data.latency === 'number') setLatency(data.latency);
          if (typeof data.processing_time_ms === 'number') setLatency(data.processing_time_ms);
          setProcessing(true);
          incrementFrame();
          break;
        }

        case 'event':
        case 'alert': {
          // Decision engine event
          addEvent({
            type: data.event_type || data.type || 'alert',
            severity: data.severity === 'critical' || data.severity === 'emergency'
              ? 'danger'
              : data.severity === 'warning'
                ? 'warning'
                : 'info',
            message: data.message || 'Unknown event',
            camera: data.camera || data.source || 'System',
          });
          break;
        }

        case 'status': {
          // System status update
          if (typeof data.is_processing === 'boolean') setProcessing(data.is_processing);
          break;
        }

        default:
          break;
      }
    },
    [setDetections, setFps, setLatency, setProcessing, incrementFrame, addEvent]
  );

  const ws = useWebSocket({
    url: url || WS_URL,
    onMessage: handleMessage,
    onOpen: () => setOnline(true),
    onClose: () => {
      setProcessing(false);
      setOnline(false);
    },
    reconnectInterval: 3000,
    maxRetries: 50,
  });

  return ws;
}
