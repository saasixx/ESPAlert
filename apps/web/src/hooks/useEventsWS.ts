import { useEffect, useState, useRef, useCallback } from 'react';
import type { AlertEvent } from '@/types/events';

/** Estado de la conexión WebSocket. */
export type ConnectionState = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

/**
 * Hook de WebSocket para recibir eventos de alerta en tiempo real.
 *
 * Se conecta al endpoint WS del backend y actualiza la lista de eventos
 * automáticamente. Incluye:
 * - Reconexión con backoff exponencial (1s → 30s).
 * - Heartbeat bidireccional (responde pong a pings del server).
 * - Estado de conexión granular (connecting, connected, reconnecting, disconnected).
 */
export function useEventsWS(initialEvents: AlertEvent[]) {
  const [events, setEvents] = useState<AlertEvent[]>(initialEvents);
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);

  const isConnected = connectionState === 'connected';

  useEffect(() => {
    // Sincronización inicial desde props
    if (initialEvents.length > 0 && events.length === 0) {
      setEvents(initialEvents);
    }
  }, [initialEvents]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let attempt = 0;
    let disposed = false;

    const connect = () => {
      if (disposed) return;

      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/events';
      setConnectionState(attempt === 0 ? 'connecting' : 'reconnecting');

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (disposed) { ws.close(); return; }
          setConnectionState('connected');
          attempt = 0;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Responder heartbeats del servidor
            if (data.type === 'ping') {
              ws.send(JSON.stringify({ type: 'pong', timestamp: new Date().toISOString() }));
              return;
            }

            const newEvent = data as AlertEvent;
            if (!newEvent.id) return;

            setEvents(prev => {
              // Evitar duplicados
              if (prev.some(e => e.id === newEvent.id)) return prev;
              // Añadir al principio, mantener máx. 500 en memoria
              return [newEvent, ...prev].slice(0, 500);
            });
          } catch (err) {
            console.error('Error al parsear mensaje WS:', err);
          }
        };

        ws.onclose = () => {
          if (disposed) return;
          setConnectionState('disconnected');
          // Reconexión con backoff exponencial
          const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
          attempt++;
          reconnectTimeout = setTimeout(connect, delay);
        };

        ws.onerror = (err) => {
          console.error('Error WS:', err);
          ws.close();
        };
      } catch (err) {
        console.error('Fallo de conexión WS:', err);
        if (!disposed) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
          attempt++;
          reconnectTimeout = setTimeout(connect, delay);
        }
      }
    };

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { events, isConnected, connectionState };
}