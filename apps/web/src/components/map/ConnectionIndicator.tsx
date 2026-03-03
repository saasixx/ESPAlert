"use client";

/**
 * ConnectionIndicator — Badge superpuesto en el mapa que muestra
 * el estado de la conexión WebSocket.
 */

import { clsx } from "clsx";

interface ConnectionIndicatorProps {
  isConnected: boolean;
  connectionState?: string;
}

export function ConnectionIndicator({
  isConnected,
  connectionState = isConnected ? "connected" : "disconnected",
}: ConnectionIndicatorProps) {
  const stateConfig: Record<string, { dot: string; text: string; label: string }> = {
    connected: {
      dot: "bg-green-500",
      text: "text-green-700 dark:text-green-400",
      label: "En vivo",
    },
    connecting: {
      dot: "bg-yellow-500 animate-pulse",
      text: "text-yellow-700 dark:text-yellow-400",
      label: "Conectando…",
    },
    reconnecting: {
      dot: "bg-yellow-500 animate-pulse",
      text: "text-yellow-700 dark:text-yellow-400",
      label: "Reconectando…",
    },
    polling: {
      dot: "bg-blue-500",
      text: "text-blue-700 dark:text-blue-400",
      label: "Actualización periódica",
    },
    disconnected: {
      dot: "bg-yellow-500",
      text: "text-yellow-700 dark:text-yellow-400",
      label: "Conectando…",
    },
  };

  const config = stateConfig[connectionState] ?? stateConfig.disconnected;

  return (
    <div className="absolute top-3 left-3 z-10">
      <div className="flex items-center gap-1.5 rounded-full bg-background/80 backdrop-blur-sm border px-2.5 py-1 text-xs shadow-sm">
        <span className={clsx("h-2 w-2 rounded-full", config.dot)} />
        <span className={clsx("font-medium", config.text)}>
          {config.label}
        </span>
      </div>
    </div>
  );
}
