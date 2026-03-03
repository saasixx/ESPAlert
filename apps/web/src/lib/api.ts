/** Wrapper para llamadas a la API del backend. */

const API_BASE =
  typeof window === "undefined"
    ? process.env.API_URL || "http://127.0.0.1:8000/api/v1"
    : "/api/v1";

interface FetchOptions extends RequestInit {
  /** Token JWT para autenticación. */
  token?: string;
}

/**
 * Fetch wrapper con base URL y auth headers automáticos.
 * En SSR usa la URL interna (API_URL), en cliente usa proxy relativo.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    ...rest,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}
