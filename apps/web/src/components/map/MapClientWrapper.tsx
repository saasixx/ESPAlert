"use client";

import ESPAlertMap from "./ESPAlertMap";
import { useEventsWS } from "@/hooks/useEventsWS";
import { AlertEvent } from "@/types/events";

export default function MapClientWrapper({ initialEvents } : { initialEvents: AlertEvent[] }) {
    const { events } = useEventsWS(initialEvents);

    return <ESPAlertMap events={events} />
}