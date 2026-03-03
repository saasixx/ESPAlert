import { useEffect, useState, useRef } from 'react';
import type { AlertEvent } from '@/types/events';

/**
 * Hook de WebSocket para recibir eventos de alerta en tiempo real.
 *
 * Se conecta al endpoint WS del backend y actualiza la lista de eventos
 * automáticamente. Incluye reconexión con backoff exponencial.
 */
export function useEventsWS(initialEvents: AlertEvent[]) {
  const [events, setEvents] = useState<AlertEvent[]>(initialEvents);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Sincronización inicial desde props
    if (initialEvents.length > 0 && events.length === 0) {
      setEvents(initialEvents);
    }
  }, [initialEvents]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let attempt = 0;

    const connect = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/events';
      
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          attempt = 0;
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'ping') return;

            const newEvent = data as AlertEvent;
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
          setIsConnected(false);
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
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return { events, isConnected };
}