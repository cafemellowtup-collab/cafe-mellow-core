"use client";

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";

export type User = {
  id: string;
  name: string;
  email: string;
  org_id: string;
  org_name: string;
  role: string;
};

type AuthContextType = {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ ok: boolean; error?: string }>;
  signup: (name: string, email: string, password: string, phone?: string, orgName?: string) => Promise<{ ok: boolean; error?: string }>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "titan.auth.token";
const USER_KEY = "titan.auth.user";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      const storedUser = localStorage.getItem(USER_KEY);
      return storedUser ? (JSON.parse(storedUser) as User) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(() => {
    if (typeof window === "undefined") return true;
    try {
      return !!(localStorage.getItem(TOKEN_KEY) && localStorage.getItem(USER_KEY));
    } catch {
      return false;
    }
  });

  useEffect(() => {
    if (!token || !user) return;

    fetch(`${API_BASE}/api/v1/auth/verify`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data?.valid) {
          try {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
          } catch {
            // ignore
          }
          setToken(null);
          setUser(null);
        }
      })
      .catch(() => {
        // API error, keep local auth (offline mode)
      })
      .finally(() => setIsLoading(false));
  }, [token, user]);

  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        return { ok: false, error: data.detail || "Login failed" };
      }
      
      if (data.ok && data.token && data.user) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        return { ok: true };
      }
      
      return { ok: false, error: data.message || "Login failed" };
    } catch {
      return { ok: false, error: "Network error. Please try again." };
    }
  }, []);

  const signup = useCallback(async (
    name: string, 
    email: string, 
    password: string, 
    phone?: string, 
    orgName?: string
  ) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          name, 
          email, 
          password, 
          phone: phone || null,
          org_name: orgName || "My Organization"
        })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        return { ok: false, error: data.detail || "Signup failed" };
      }
      
      if (data.ok && data.token && data.user) {
        setToken(data.token);
        setUser(data.user);
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));
        return { ok: true };
      }
      
      return { ok: false, error: data.message || "Signup failed" };
    } catch {
      return { ok: false, error: "Network error. Please try again." };
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      // ignore
    }
    
    // Call logout endpoint (fire and forget)
    fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }).catch(() => {});
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        signup,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
