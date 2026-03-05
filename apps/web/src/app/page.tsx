import MapClientWrapper from "@/components/map/MapClientWrapper";

export const revalidate = 60; // Revalidate every minute

/** Fetches active events from the backend (SSR). */
async function getActiveEvents() {
  try {
    // NEXT_PUBLIC_API_URL includes /api/v1; API_URL is just the host base
    const host = process.env.API_URL || "http://127.0.0.1:8000";
    const apiBase = process.env.NEXT_PUBLIC_API_URL || `${host}/api/v1`;
    const res = await fetch(`${apiBase}/events/`, {
      next: { revalidate: 60 },
    });

    if (!res.ok) {
      if (process.env.NODE_ENV !== "production") {
        console.warn("Could not fetch events from backend:", res.status);
      }
      return [];
    }

    return await res.json();
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.error("Error fetching events:", error);
    }
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
