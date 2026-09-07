"use client";

import type { ReactNode } from "react";
import { DocumentsProvider } from "./documents-context";
import { HealthProvider } from "./health-context";
import { UploadModalProvider } from "./upload-modal-context";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <HealthProvider>
      <DocumentsProvider>
        <UploadModalProvider>{children}</UploadModalProvider>
      </DocumentsProvider>
    </HealthProvider>
  );
}
