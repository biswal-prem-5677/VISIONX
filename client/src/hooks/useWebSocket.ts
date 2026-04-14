/**
 * VisionX — WebSocket Hook
 * Real-time connection to FastAPI backend
 */

import { useEffect, useRef, useCallback, useState } from 'react';

interface WebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

interface WebSocketState {
  isConnected: boolean;
  lastMessage: any;
  error: string | null;
  retryCount: number;
}

export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxRetries = 10,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    lastMessage: null,
    error: null,
    retryCount: 0,
  });

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        retryCountRef.current = 0;
        setState((s) => ({ ...s, isConnected: true, error: null, retryCount: 0 }));
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setState((s) => ({ ...s, lastMessage: data }));
          onMessage?.(data);
        } catch {
          setState((s) => ({ ...s, lastMessage: event.data }));
          onMessage?.(event.data);
        }
      };

      ws.onclose = () => {
        setState((s) => ({ ...s, isConnected: false }));
        onClose?.();

        // Auto-reconnect
        if (retryCountRef.current < maxRetries) {
          retryCountRef.current += 1;
          setState((s) => ({ ...s, retryCount: retryCountRef.current }));
          reconnectTimerRef.current = setTimeout(connect, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        setState((s) => ({ ...s, error: 'WebSocket connection error' }));
        onError?.(error);
      };

      wsRef.current = ws;
    } catch (err) {
      setState((s) => ({ ...s, error: String(err) }));
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnectInterval, maxRetries]);

  const sendMessage = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { ...state, sendMessage, disconnect, reconnect: connect };
}
