/** Wrapper for backend API calls. */

interface ResolveApiBaseUrlOptions {
  /** Override browser detection for tests. */
  isBrowser?: boolean;
  /** Override public API URL for tests. */
  nextPublicApiUrl?: string;
  /** Override internal API host URL for tests. */
  apiUrl?: string;
}

/** Resolves API base URL for SSR/client contexts. */
export function resolveApiBaseUrl(options: ResolveApiBaseUrlOptions = {}): string {
  const isBrowser = options.isBrowser ?? typeof window !== "undefined";
  const nextPublicApiUrl = options.nextPublicApiUrl ?? process.env.NEXT_PUBLIC_API_URL;
  const apiUrl = options.apiUrl ?? process.env.API_URL;

  if (nextPublicApiUrl) {
    return nextPublicApiUrl;
  }

  if (isBrowser) {
    return "/api/v1";
  }

  const host = apiUrl || "http://127.0.0.1:8000";
  return `${host}/api/v1`;
}

/** API base URL: SSR uses internal variable, client uses proxy or public URL. */
const API_BASE = resolveApiBaseUrl();

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
