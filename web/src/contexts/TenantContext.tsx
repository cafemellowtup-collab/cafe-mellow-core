"use client";

import { createContext, useContext, useState, ReactNode } from "react";

export type TenantConfig = {
  org_id: string;
  location_id: string;
  org_name: string;
  location_name: string;
};

type TenantContextType = {
  tenant: TenantConfig;
  setTenant: (tenant: TenantConfig) => void;
  availableLocations: TenantConfig[];
};

const TenantContext = createContext<TenantContextType | undefined>(undefined);

const STORAGE_KEY = "titan.tenant.config";

// Default available outlets (can be fetched from API later)
const DEFAULT_LOCATIONS: TenantConfig[] = [
  {
    org_id: "cafe_mellow",
    location_id: "koramangala",
    org_name: "Cafe Mellow",
    location_name: "Koramangala",
  },
  {
    org_id: "cafe_mellow",
    location_id: "indiranagar",
    org_name: "Cafe Mellow",
    location_name: "Indiranagar",
  },
  {
    org_id: "cafe_mellow",
    location_id: "whitefield",
    org_name: "Cafe Mellow",
    location_name: "Whitefield",
  },
];

export function TenantProvider({ children }: { children: ReactNode }) {
  const [tenant, setTenantState] = useState<TenantConfig>(() => {
    if (typeof window === "undefined") return DEFAULT_LOCATIONS[0];
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored) as TenantConfig;
      }
    } catch {
      // ignore
    }
    return DEFAULT_LOCATIONS[0];
  });
  const [availableLocations] = useState<TenantConfig[]>(DEFAULT_LOCATIONS);

  const setTenant = (newTenant: TenantConfig) => {
    setTenantState(newTenant);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newTenant));
    } catch {
      // ignore
    }
  };

  return (
    <TenantContext.Provider value={{ tenant, setTenant, availableLocations }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error("useTenant must be used within TenantProvider");
  }
  return context;
}
