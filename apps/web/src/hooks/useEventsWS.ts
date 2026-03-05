import { useEffect, useState, useRef, useCallback } from 'react';
import type { AlertEvent } from '@/types/events';

/** WebSocket connection state. */
export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'polling' | 'disconnected';

/**
 * WebSocket hook for receiving real-time alert events.
 *
 * Connects to the backend WS endpoint and updates the event list
 * automatically. Includes:
 * - Reconnection with exponential backoff (1s → 30s).
 * - Bidirectional heartbeat (responds pong to server pings).
 * - HTTP polling fallback when WS is unavailable (e.g. Vercel).
 * - Granular connection state.
 */
export function useEventsWS(initialEvents: AlertEvent[]) {
  const [events, setEvents] = useState<AlertEvent[]>(initialEvents);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsFailCount = useRef(0);

  const isConnected = connectionState === 'connected' || connectionState === 'polling';

  // Sync initial events from SSR props (no effect needed — just initialise state)
  if (initialEvents.length > 0 && events.length === 0) {
    setEvents(initialEvents);
  }

  // Polling fallback — fetches events via HTTP API
  const startPolling = useCallback(() => {
    if (pollingRef.current) return; // Already polling

    setConnectionState('polling');

    const poll = async () => {
      try {
        const resp = await fetch('/api/v1/events/?limit=200');
        if (resp.ok) {
          const data: AlertEvent[] = await resp.json();
          setEvents(data);
        }
      } catch (err) {
        console.error('Error polling events:', err);
      }
    };

    // Poll immediately then every 60 seconds
    poll();
    pollingRef.current = setInterval(poll, 60_000);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let disposed = false;

    const connect = () => {
      if (disposed) return;

      // After 3 WS failures, switch to polling permanently
      if (wsFailCount.current >= 3) {
        startPolling();
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const wsProtocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL
        || (apiUrl ? apiUrl.replace(/^https?:/, wsProtocol) + '/ws/events' : `${wsProtocol}//${window.location.host}/api/v1/ws/events`);
      setConnectionState(wsFailCount.current === 0 ? 'connecting' : 'reconnecting');

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (disposed) { ws.close(); return; }
          setConnectionState('connected');
          wsFailCount.current = 0;
          stopPolling();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Respond to server heartbeats
            if (data.type === 'ping') {
              ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
              return;
            }

            const newEvent = data as AlertEvent;
            if (!newEvent.id) return;

            setEvents(prev => {
              // Evitar duplicados
              if (prev.some(e => e.id === newEvent.id)) return prev;
              // Prepend new event, keep max 500 in memory
              return [newEvent, ...prev].slice(0, 500);
            });
          } catch (err) {
            console.error('Error al parsear mensaje WS:', err);
          }
        };

        ws.onclose = () => {
          if (disposed) return;
          wsFailCount.current++;

          if (wsFailCount.current >= 3) {
            // Switch to polling after 3 failures
            startPolling();
          } else {
            setConnectionState('reconnecting');
            const delay = Math.min(1000 * Math.pow(2, wsFailCount.current), 15000);
            reconnectTimeout = setTimeout(connect, delay);
          }
        };

        ws.onerror = (err) => {
          console.error('Error WS:', err);
          ws.close();
        };
      } catch (err) {
        console.error('Fallo de conexión WS:', err);
        wsFailCount.current++;
        if (!disposed) {
          if (wsFailCount.current >= 3) {
            startPolling();
          } else {
            const delay = Math.min(1000 * Math.pow(2, wsFailCount.current), 15000);
            reconnectTimeout = setTimeout(connect, delay);
          }
        }
      }
    };

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectTimeout);
      stopPolling();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { events, isConnected, connectionState };
}