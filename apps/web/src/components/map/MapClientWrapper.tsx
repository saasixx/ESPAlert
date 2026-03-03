"use client";

import type { AlertEvent } from "@/types/events";
import { useEventsWS } from "@/hooks/useEventsWS";
import ESPAlertMap from "./ESPAlertMap";

/**
 * Wrapper cliente que conecta los eventos en tiempo real (WS)
 * con el componente del mapa.
 */
export default function MapClientWrapper({ initialEvents }: { initialEvents: AlertEvent[] }) {
  const { events, isConnected } = useEventsWS(initialEvents);
  return <ESPAlertMap events={events} isConnected={isConnected} />;
}