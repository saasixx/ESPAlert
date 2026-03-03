"use client";

import type { AlertEvent } from "@/types/events";
import { useEventsWS } from "@/hooks/useEventsWS";
import AlertMap from "./AlertMap";

/**
 * Wrapper cliente que conecta los eventos en tiempo real (WS)
 * con el componente del mapa basado en mapcn.
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