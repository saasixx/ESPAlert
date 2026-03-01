import MapClientWrapper from "@/components/map/MapClientWrapper";

export const revalidate = 60; // Revalidate every minute

async function getActiveEvents() {
  try {
    // For local dev, we try to fetch from the local backend if available
    const apiBase = process.env.API_URL || "http://127.0.0.1:8000/api/v1";
    const res = await fetch(`${apiBase}/events/`, { 
      next: { revalidate: 60 } 
    });
    
    if (!res.ok) {
      console.warn("Failed to fetch events from backend:", res.status);
      return [];
    }
    
    const data = await res.json();
    return data;
  } catch (error) {
    console.error("Error fetching events:", error);
    return [];
  }
}

export default async function Home() {
  const initialEvents = await getActiveEvents();

  return (
    <main className="w-full h-[100dvh] relative overflow-hidden bg-background">
      <MapClientWrapper initialEvents={initialEvents} />
    </main>
  );
}
