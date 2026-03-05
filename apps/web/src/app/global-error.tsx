"use client";

/**
 * Global error handler — catches unhandled client-side exceptions
 * and shows useful debugging information.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="es">
      <body className="flex items-center justify-center h-screen bg-zinc-950 text-white font-mono p-8">
        <div className="max-w-xl space-y-4">
          <h1 className="text-2xl font-bold text-red-400">Error de aplicación</h1>
          <p className="text-zinc-400">Se ha producido un error inesperado:</p>
          <pre className="bg-zinc-900 rounded p-4 text-sm overflow-auto max-h-60 text-red-300">
            {error.message}
          </pre>
          {error.digest && (
            <p className="text-xs text-zinc-500">Digest: {error.digest}</p>
          )}
          <button
            onClick={reset}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition"
          >
            Reintentar
          </button>
        </div>
      </body>
    </html>
  );
}
