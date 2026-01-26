"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";

type UserRole = "ceo" | "manager" | "staff" | "viewer";

type Permission = 
  | "view_dashboard"
  | "view_chat"
  | "view_operations"
  | "view_settings"
  | "edit_credentials"
  | "trigger_sync"
  | "delete_data"
  | "view_financials"
  | "export_reports"
  | "manage_users";

type RBACContextType = {
  role: UserRole;
  setRole: (role: UserRole) => void;
  hasPermission: (permission: Permission) => boolean;
  permissions: Permission[];
};

const RBACContext = createContext<RBACContextType | undefined>(undefined);

const rolePermissions: Record<UserRole, Permission[]> = {
  ceo: [
    "view_dashboard",
    "view_chat",
    "view_operations",
    "view_settings",
    "edit_credentials",
    "trigger_sync",
    "delete_data",
    "view_financials",
    "export_reports",
    "manage_users",
  ],
  manager: [
    "view_dashboard",
    "view_chat",
    "view_operations",
    "view_settings",
    "trigger_sync",
    "view_financials",
    "export_reports",
  ],
  staff: [
    "view_dashboard",
    "view_chat",
    "view_operations",
  ],
  viewer: [
    "view_dashboard",
  ],
};

export function RBACProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<UserRole>("ceo");
  
  // Load role from localStorage on mount
  useEffect(() => {
    const savedRole = localStorage.getItem("titan_user_role");
    if (savedRole && (savedRole === "ceo" || savedRole === "manager" || savedRole === "staff" || savedRole === "viewer")) {
      setRole(savedRole);
    }
  }, []);
  
  // Save role to localStorage when changed
  useEffect(() => {
    localStorage.setItem("titan_user_role", role);
  }, [role]);
  
  const hasPermission = (permission: Permission): boolean => {
    return rolePermissions[role].includes(permission);
  };
  
  const permissions = rolePermissions[role];
  
  return (
    <RBACContext.Provider value={{ role, setRole, hasPermission, permissions }}>
      {children}
    </RBACContext.Provider>
  );
}

export function useRBAC() {
  const context = useContext(RBACContext);
  if (!context) {
    throw new Error("useRBAC must be used within RBACProvider");
  }
  return context;
}

// HOC for permission-based rendering
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  requiredPermission: Permission,
  fallback?: ReactNode
) {
  return function PermissionGatedComponent(props: P) {
    const { hasPermission } = useRBAC();
    
    if (!hasPermission(requiredPermission)) {
      return fallback || (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-center">
          <div className="text-sm font-semibold text-red-200">Access Denied</div>
          <div className="mt-1 text-xs text-red-300">
            You don't have permission to access this feature
          </div>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
}
