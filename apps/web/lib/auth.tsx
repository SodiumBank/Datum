"use client";

import { createContext, useContext, useState, ReactNode } from "react";

/**
 * Basic Auth & Role Stubs (Sprint 8 - Story 8).
 * Minimal auth scaffolding to distinguish roles.
 */

export type UserRole = "CUSTOMER" | "OPS" | "ADMIN";

interface AuthContextType {
  role: UserRole | null;
  userId: string | null;
  setRole: (role: UserRole, userId: string) => void;
  hasRole: (requiredRole: UserRole | UserRole[]) => boolean;
  canEdit: () => boolean;
  canApprove: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<UserRole | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  const setRole = (newRole: UserRole, newUserId: string) => {
    setRoleState(newRole);
    setUserId(newUserId);
  };

  const hasRole = (requiredRole: UserRole | UserRole[]): boolean => {
    if (!role) return false;
    if (Array.isArray(requiredRole)) {
      return requiredRole.includes(role);
    }
    return role === requiredRole;
  };

  const canEdit = (): boolean => {
    return hasRole(["CUSTOMER", "OPS", "ADMIN"]);
  };

  const canApprove = (): boolean => {
    return hasRole(["OPS", "ADMIN"]);
  };

  return (
    <AuthContext.Provider value={{ role, userId, setRole, hasRole, canEdit, canApprove }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    // Default to CUSTOMER role if context not available (backwards compatibility)
    return {
      role: "CUSTOMER" as UserRole,
      userId: "customer_001",
      setRole: () => {},
      hasRole: () => true,
      canEdit: () => true,
      canApprove: () => false,
    };
  }
  return context;
}
