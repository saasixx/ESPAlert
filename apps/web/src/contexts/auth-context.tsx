"use client";

/**
 * AuthContext — client-side authentication state management.
 *
 * Stores the JWT token in localStorage and hydrates the user profile
 * on mount via GET /api/v1/auth/me.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { apiFetch } from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
  quiet_start: string | null;
  quiet_end: string | null;
  predictive_alerts: boolean;
  created_at: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    displayName?: string,
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// ── Context ────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

const TOKEN_KEY = "espalert_token";

// ── Provider ───────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Initialize token from localStorage without calling setState inside an effect
  const [token, setToken] = useState<string | null>(() =>
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null,
  );
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async (t: string) => {
    try {
      const u = await apiFetch<AuthUser>("/auth/me", { token: t });
      setUser(u);
    } catch {
      // Token invalid or expired — clear it
      localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
    }
  }, []);

  // Hydrate user profile on mount if token exists
  useEffect(() => {
    if (token) {
      fetchUser(token).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await apiFetch<{ access_token: string }>(
        "/auth/login",
        {
          method: "POST",
          body: JSON.stringify({ email, password }),
        },
      );
      localStorage.setItem(TOKEN_KEY, access_token);
      setToken(access_token);
      await fetchUser(access_token);
    },
    [fetchUser],
  );

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const { access_token } = await apiFetch<{ access_token: string }>(
        "/auth/register",
        {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
            display_name: displayName || null,
          }),
        },
      );
      localStorage.setItem(TOKEN_KEY, access_token);
      setToken(access_token);
      await fetchUser(access_token);
    },
    [fetchUser],
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (token) await fetchUser(token);
  }, [token, fetchUser]);

  return (
    <AuthContext.Provider
      value={{ user, token, isLoading, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── Hook ───────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
