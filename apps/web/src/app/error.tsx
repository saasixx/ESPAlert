"use client";

/**
 * Error boundary for the root route — catches errors on the main page.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex items-center justify-center h-dvh bg-background text-foreground p-8">
      <div className="max-w-xl space-y-4 text-center">
        <h1 className="text-2xl font-bold text-red-500">Error al cargar ESPAlert</h1>
        <p className="text-muted-foreground">Se ha producido un error en el cliente:</p>
        <pre className="bg-muted rounded p-4 text-sm overflow-auto max-h-60 text-left text-red-400">
          {error.message}
        </pre>
        {error.stack && (
          <details className="text-left">
            <summary className="text-xs text-muted-foreground cursor-pointer">Stack trace</summary>
            <pre className="bg-muted rounded p-2 text-xs overflow-auto max-h-40 mt-1">
              {error.stack}
            </pre>
          </details>
        )}
        <button
          onClick={reset}
          className="px-4 py-2 bg-primary text-primary-foreground rounded hover:opacity-90 transition"
        >
          Reintentar
        </button>
      </div>
    </main>
  );
}
