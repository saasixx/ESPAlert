import { useEffect, useState, useRef } from 'react';
import type { AlertEvent } from '@/types/events';

export function useEventsWS(initialEvents: AlertEvent[]) {
  const [events, setEvents] = useState<AlertEvent[]>(initialEvents);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial sync from props
    if (initialEvents.length > 0 && events.length === 0) {
      setEvents(initialEvents);
    }
  }, [initialEvents]);

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
          console.log('Connected to ESPAlert WS');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'ping') return;
            
            const newEvent = data as AlertEvent;
            setEvents(prev => {
              // Avoid duplicates
              if (prev.some(e => e.id === newEvent.id)) return prev;
              
              // Add to top, keep only last 500 in memory
              return [newEvent, ...prev].slice(0, 500);
            });
          } catch (err) {
            console.error('Failed to parse WS message', err);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          // Exponential backoff reconnect
          const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
          attempt++;
          reconnectTimeout = setTimeout(connect, delay);
        };

        ws.onerror = (err) => {
          console.error('WS Error:', err);
          ws.close();
        };
      } catch (err) {
        console.error('WS Connection failed:', err);
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