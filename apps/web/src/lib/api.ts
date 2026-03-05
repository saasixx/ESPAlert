/** Wrapper for backend API calls. */

/** API base URL: SSR uses internal variable, client uses proxy or public URL. */
const API_BASE =
  typeof window === "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || `${process.env.API_URL || "http://127.0.0.1:8000"}/api/v1`
    : process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface FetchOptions extends RequestInit {
  /** JWT token for authentication. */
  token?: string;
}

/**
 * Fetch wrapper with base URL and automatic auth headers.
 * In SSR uses internal URL (API_URL), in client uses relative proxy.
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
