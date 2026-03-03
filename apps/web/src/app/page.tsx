import MapClientWrapper from "@/components/map/MapClientWrapper";

export const revalidate = 60; // Revalidar cada minuto

/** Obtiene los eventos activos desde el backend (SSR). */
async function getActiveEvents() {
  try {
    // NEXT_PUBLIC_API_URL incluye /api/v1; API_URL es solo el host base
    const host = process.env.API_URL || "http://127.0.0.1:8000";
    const apiBase = process.env.NEXT_PUBLIC_API_URL || `${host}/api/v1`;
    const res = await fetch(`${apiBase}/events/`, {
      next: { revalidate: 60 },
    });

    if (!res.ok) {
      console.warn("No se pudieron obtener eventos del backend:", res.status);
      return [];
    }

    return await res.json();
  } catch (error) {
    console.error("Error al obtener eventos:", error);
    return [];
  }
}

export default async function Home() {
  const initialEvents = await getActiveEvents();

  return (
    <main className="w-full h-dvh relative overflow-hidden bg-background">
      <MapClientWrapper initialEvents={initialEvents} />
    </main>
  );
}
