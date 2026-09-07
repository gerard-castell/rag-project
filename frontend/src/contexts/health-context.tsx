"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { health } from "@/lib/api";

const HealthContext = createContext<boolean | null>(null);

const HEALTH_POLL_MS = 15000;

export function HealthProvider({ children }: { children: ReactNode }) {
  const [healthOk, setHealthOk] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const checkHealth = () => {
      health()
        .then(() => {
          if (!cancelled) setHealthOk(true);
        })
        .catch(() => {
          if (!cancelled) setHealthOk(false);
        });
    };
    checkHealth();
    const interval = setInterval(checkHealth, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <HealthContext.Provider value={healthOk}>{children}</HealthContext.Provider>
  );
}

export function useHealth(): boolean {
  const ctx = useContext(HealthContext);
  if (ctx === null) {
    throw new Error("useHealth must be used within a HealthProvider");
  }
  return ctx;
}
