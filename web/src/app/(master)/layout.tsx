"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useState } from "react";
import { 
  LayoutDashboard, 
  Users, 
  DollarSign, 
  Activity, 
  ToggleLeft, 
  Brain, 
  Bell, 
  Settings,
  LogOut,
  Shield,
  ChevronLeft,
  Menu
} from "lucide-react";

function NavItem({ href, label, icon: Icon, badge }: { 
  href: string; 
  label: string; 
  icon: React.ElementType;
  badge?: number;
}) {
  const pathname = usePathname();
  const active = pathname === href || (href !== "/master" && pathname?.startsWith(href));

  return (
    <Link
      href={href}
      className={
        "group flex items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-sm transition " +
        (active
          ? "bg-gradient-to-r from-violet-500/20 to-purple-500/20 text-white ring-1 ring-violet-400/40"
          : "text-zinc-300 hover:bg-zinc-800/50 hover:text-white")
      }
    >
      <div className="flex items-center gap-3">
        <Icon size={18} className={active ? "text-violet-400" : "text-zinc-500 group-hover:text-violet-300"} />
        <span className="font-medium">{label}</span>
      </div>
      {badge && badge > 0 ? (
        <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-[11px] font-medium text-red-200 ring-1 ring-red-400/30">
          {badge}
        </span>
      ) : null}
    </Link>
  );
}

export default function MasterLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-purple-950/30 text-zinc-50">
      {/* Background effects */}
      <div className="pointer-events-none fixed inset-0 opacity-40" aria-hidden>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(139,92,246,0.15),transparent_40%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_80%,rgba(168,85,247,0.1),transparent_35%)]" />
      </div>

      <div className="relative flex min-h-screen">
        {/* Sidebar */}
        <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} shrink-0 border-r border-white/5 bg-black/40 backdrop-blur-xl transition-all duration-300`}>
          <div className="sticky top-0 flex h-screen flex-col p-4">
            {/* Header */}
            <div className="mb-6 flex items-center justify-between">
              {sidebarOpen && (
                <div>
                  <div className="flex items-center gap-2">
                    <Shield size={20} className="text-violet-400" />
                    <span className="text-lg font-bold text-white">Master</span>
                  </div>
                  <div className="text-xs text-zinc-500">Super Admin Control</div>
                </div>
              )}
              <button 
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white"
              >
                {sidebarOpen ? <ChevronLeft size={18} /> : <Menu size={18} />}
              </button>
            </div>

            {/* Navigation */}
            {sidebarOpen && (
              <nav className="flex-1 space-y-1">
                <NavItem href="/master" label="Overview" icon={LayoutDashboard} />
                <NavItem href="/master/tenants" label="Tenants" icon={Users} />
                <NavItem href="/master/usage" label="Usage & Costs" icon={DollarSign} />
                <NavItem href="/master/health" label="Health Monitor" icon={Activity} />
                <NavItem href="/master/features" label="Feature Flags" icon={ToggleLeft} />
                <NavItem href="/master/ai-watchdog" label="AI Watchdog" icon={Brain} badge={3} />
                <NavItem href="/master/alerts" label="Alerts" icon={Bell} badge={2} />
                <NavItem href="/master/settings" label="Settings" icon={Settings} />
              </nav>
            )}

            {/* Footer */}
            {sidebarOpen && (
              <div className="mt-auto space-y-3 border-t border-white/5 pt-4">
                <div className="rounded-xl border border-violet-500/20 bg-violet-500/10 p-3">
                  <div className="text-xs font-medium text-violet-200">System Status</div>
                  <div className="mt-1 flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]" />
                    <span className="text-sm text-white">All Systems Operational</span>
                  </div>
                </div>
                
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-300 transition hover:bg-white/10"
                >
                  <LogOut size={16} />
                  <span>Exit to Tenant View</span>
                </Link>
              </div>
            )}
          </div>
        </aside>

        {/* Main Content */}
        <div className="flex min-w-0 flex-1 flex-col">
          {/* Top Bar */}
          <header className="sticky top-0 z-20 border-b border-white/5 bg-black/40 backdrop-blur-xl">
            <div className="flex items-center justify-between px-6 py-4">
              <div>
                <h1 className="text-xl font-semibold text-white">TITAN Master Dashboard</h1>
                <p className="text-sm text-zinc-400">Complete control over all tenants and system operations</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-1.5 text-xs font-medium text-violet-200">
                  Super Admin
                </div>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
