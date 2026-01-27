"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";
import { LogOut, User } from "lucide-react";
import NotificationCenter from "./NotificationCenter";
import { useAuth } from "@/contexts/AuthContext";

function NavItem({ href, label, badge }: { href: string; label: string; badge?: string }) {
  const pathname = usePathname();
  const active = pathname === href || (href !== "/" && pathname?.startsWith(href));

  return (
    <Link
      href={href}
      className={
        "group flex items-center justify-between gap-3 rounded-xl px-3 py-2 text-sm transition " +
        (active
          ? "bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 text-white ring-1 ring-emerald-400/40"
          : "text-zinc-300 hover:bg-zinc-900 hover:text-white ring-1 ring-transparent")
      }
    >
      <div className="flex items-center gap-3">
        <span
          className={
            "h-2 w-2 rounded-full transition " +
            (active ? "bg-emerald-400 shadow-[0_0_0_6px_rgba(16,185,129,0.15)]" : "bg-zinc-700 group-hover:bg-emerald-300")
          }
        />
        <span className="font-semibold tracking-tight">{label}</span>
      </div>
      {badge ? (
        <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[11px] font-medium text-emerald-200 ring-1 ring-emerald-400/30">
          {badge}
        </span>
      ) : null}
    </Link>
  );
}

export default function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { user, logout, isAuthenticated } = useAuth();

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-950 to-black/90 text-zinc-50">
      <div className="pointer-events-none fixed inset-0 opacity-60" aria-hidden>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(52,211,153,0.12),transparent_35%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_0%,rgba(59,130,246,0.18),transparent_30%)]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-[1680px] px-3 lg:px-6">
        <aside className="hidden w-72 shrink-0 border-r border-white/5 bg-white/5 backdrop-blur-xl lg:block">
          <div className="sticky top-0 space-y-4 p-4">
            <div className="rounded-2xl border border-white/10 bg-white/10 p-4 shadow-lg shadow-emerald-500/5">
              <div className="text-xs uppercase tracking-[0.2em] text-emerald-200/80">Titan</div>
              <div className="mt-2 text-lg font-semibold tracking-tight text-white">Cafe AI Business OS</div>
              <div className="mt-2 text-sm text-zinc-300">Executive cockpit for revenue, ops, and CX.</div>
            </div>

            <nav className="space-y-1">
              <NavItem href="/chat" label="Chat" badge="Live" />
              <NavItem href="/dashboard" label="Dashboard" />
              <NavItem href="/operations" label="Operations" />
              <NavItem href="/operations/quarantine" label="Quarantine" />
              <NavItem href="/settings" label="Settings" />
            </nav>

            <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-emerald-500/10 via-cyan-500/5 to-sky-500/10 p-4 text-sm text-zinc-200 shadow-lg shadow-emerald-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/70">Status</div>
                  <div className="mt-1 font-semibold">API: http://127.0.0.1:8000</div>
                </div>
                <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_6px_rgba(52,211,153,0.15)]" />
              </div>
              <div className="mt-2 text-xs text-emerald-100/80">Next: ship to Cloud Run & Vercel</div>
            </div>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b border-white/10 bg-black/60 backdrop-blur-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 lg:px-6">
              <div className="min-w-0">
                <div className="text-xs uppercase tracking-[0.24em] text-emerald-200">Titan ERP</div>
                <div className="text-lg font-semibold leading-tight text-white">Precision intelligence for every cafe decision.</div>
                <div className="text-xs text-zinc-400">Predict revenue, optimize staff, and interrogate your data like a strategist.</div>
              </div>
              <div className="flex items-center gap-3">
                <NotificationCenter />
                {isAuthenticated && user ? (
                  <div className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-200 shadow-md shadow-emerald-500/10 md:inline-flex">
                    <User size={12} />
                    <span>{user.name || user.email}</span>
                  </div>
                ) : (
                  <div className="hidden rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-200 shadow-md shadow-emerald-500/10 md:inline-flex">
                    Guest
                  </div>
                )}
                {isAuthenticated ? (
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-zinc-300 transition hover:bg-red-500/20 hover:text-red-200 hover:border-red-500/30"
                  >
                    <LogOut size={14} />
                    <span className="hidden md:inline">Logout</span>
                  </button>
                ) : (
                  <Link 
                    href="/login"
                    className="rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2 text-xs font-semibold text-black shadow-lg shadow-emerald-500/30 transition hover:scale-[1.01]"
                  >
                    Sign In
                  </Link>
                )}
              </div>
            </div>
          </header>

          <main className="min-w-0 flex-1 p-4 lg:p-8">{children}</main>
        </div>
      </div>
    </div>
  );
}
