"use client";

import { useState, useCallback, ReactNode, createContext, useContext } from "react";
import { DatumApiError } from "./api";

/**
 * Global error handling context for API errors (Sprint 8).
 */

interface ErrorContextType {
  error: string | null;
  showError: (message: string) => void;
  clearError: () => void;
  handleApiError: (err: unknown) => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

export function ErrorProvider({ children }: { children: ReactNode }) {
  const [error, setError] = useState<string | null>(null);

  const showError = useCallback((message: string) => {
    setError(message);
    // Auto-clear after 5 seconds
    setTimeout(() => setError(null), 5000);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const handleApiError = useCallback(
    (err: unknown) => {
      if (err instanceof DatumApiError) {
        showError(err.detail || err.message);
      } else if (err instanceof Error) {
        showError(err.message);
      } else {
        showError("An unexpected error occurred");
      }
    },
    [showError]
  );

  return (
    <ErrorContext.Provider value={{ error, showError, clearError, handleApiError }}>
      {children}
      {error && (
        <div
          style={{
            position: "fixed",
            top: 16,
            right: 16,
            maxWidth: 500,
            padding: 16,
            backgroundColor: "#fee",
            border: "2px solid #fcc",
            borderRadius: 8,
            boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
            zIndex: 9999,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
            <div>
              <div style={{ fontWeight: "bold", color: "#c00", marginBottom: 4 }}>Error</div>
              <div style={{ color: "#800" }}>{error}</div>
            </div>
            <button
              onClick={clearError}
              style={{
                marginLeft: 16,
                padding: "4px 8px",
                backgroundColor: "transparent",
                border: "none",
                color: "#800",
                cursor: "pointer",
                fontSize: 18,
                lineHeight: 1,
              }}
            >
              ×
            </button>
          </div>
        </div>
      )}
    </ErrorContext.Provider>
  );
}

export function useErrorHandler() {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error("useErrorHandler must be used within ErrorProvider");
  }
  return context;
}
