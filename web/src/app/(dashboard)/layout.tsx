import { AuthProvider } from "@/contexts/AuthContext";
import { TenantProvider } from "@/contexts/TenantContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <TenantProvider>
        <ProtectedRoute>
          <AppShell>{children}</AppShell>
        </ProtectedRoute>
      </TenantProvider>
    </AuthProvider>
  );
}
