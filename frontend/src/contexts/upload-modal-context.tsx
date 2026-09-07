"use client";

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface UploadModalContextValue {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}

const UploadModalContext = createContext<UploadModalContextValue | null>(null);

export function UploadModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const value = useMemo<UploadModalContextValue>(
    () => ({
      isOpen,
      open: () => setIsOpen(true),
      close: () => setIsOpen(false),
    }),
    [isOpen]
  );

  return (
    <UploadModalContext.Provider value={value}>
      {children}
    </UploadModalContext.Provider>
  );
}

export function useUploadModal(): UploadModalContextValue {
  const ctx = useContext(UploadModalContext);
  if (!ctx) {
    throw new Error("useUploadModal must be used within an UploadModalProvider");
  }
  return ctx;
}
