"use client";

import type { AlertEvent } from "@/types/events";
import { useEventsWS } from "@/hooks/useEventsWS";
import AlertMap from "./AlertMap";

/**
 * Client wrapper that connects real-time events (WS)
 * with the mapcn-based map component.
 */
export default function MapClientWrapper({ initialEvents }: { initialEvents: AlertEvent[] }) {
  const { events, isConnected, connectionState } = useEventsWS(initialEvents);
  return (
    <AlertMap
      events={events}
      isConnected={isConnected}
      connectionState={connectionState}
    />
  );
}