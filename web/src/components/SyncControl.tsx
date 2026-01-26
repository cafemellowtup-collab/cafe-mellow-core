"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw, CheckCircle, XCircle, Loader2, Database } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

const API_PREFIX = "/api/v1";

type SyncType = "sales" | "expenses" | "recipes" | "purchases" | "wastage" | "all";

type SyncStatus = {
  status: "idle" | "queued" | "running" | "completed" | "failed";
  message: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
};

export default function SyncControl() {
  const [syncing, setSyncing] = useState<Record<SyncType, boolean>>({
    sales: false,
    expenses: false,
    recipes: false,
    purchases: false,
    wastage: false,
    all: false,
  });
  
  const [status, setStatus] = useState<Record<SyncType, SyncStatus>>({
    sales: { status: "idle", message: "" },
    expenses: { status: "idle", message: "" },
    recipes: { status: "idle", message: "" },
    purchases: { status: "idle", message: "" },
    wastage: { status: "idle", message: "" },
    all: { status: "idle", message: "" },
  });
  
  async function triggerSync(type: SyncType) {
    setSyncing(prev => ({ ...prev, [type]: true }));
    setStatus(prev => ({ 
      ...prev, 
      [type]: { status: "queued", message: "Starting sync..." } 
    }));
    
    try {
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/sync/${type}`, {
        method: "POST"
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Sync failed");
      }
      
      // Poll status
      pollSyncStatus(type);
    } catch (e: unknown) {
      setStatus(prev => ({
        ...prev,
        [type]: {
          status: "failed",
          message: e instanceof Error ? e.message : "Sync failed",
          error: e instanceof Error ? e.message : "Unknown error"
        }
      }));
      setSyncing(prev => ({ ...prev, [type]: false }));
    }
  }
  
  async function pollSyncStatus(type: SyncType) {
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    const interval = setInterval(async () => {
      attempts++;
      
      try {
        const res = await fetch(`${API_BASE_URL}${API_PREFIX}/sync/status/${type}`);
        const data = await res.json();
        
        setStatus(prev => ({
          ...prev,
          [type]: {
            status: data.status || "running",
            message: data.message || "Syncing...",
            started_at: data.started_at,
            completed_at: data.completed_at,
            error: data.error
          }
        }));
        
        if (data.status === "completed" || data.status === "failed" || attempts >= maxAttempts) {
          clearInterval(interval);
          setSyncing(prev => ({ ...prev, [type]: false }));
        }
      } catch (e) {
        clearInterval(interval);
        setSyncing(prev => ({ ...prev, [type]: false }));
      }
    }, 5000); // Poll every 5 seconds
  }
  
  const syncButtons: Array<{ type: SyncType; label: string; description: string }> = [
    { type: "sales", label: "Sales", description: "Petpooja POS data" },
    { type: "expenses", label: "Expenses", description: "Google Drive expenses" },
    { type: "recipes", label: "Recipes", description: "BOM & ingredients" },
    { type: "purchases", label: "Purchases", description: "Purchase bills" },
    { type: "wastage", label: "Wastage", description: "Loss tracking" },
  ];
  
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-zinc-100">Data Synchronization</div>
          <div className="mt-1 text-xs text-zinc-500">
            Manually sync data sources or run master sync
          </div>
        </div>
        <button
          onClick={() => triggerSync("all")}
          disabled={syncing.all}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-4 py-2 text-sm font-semibold text-black shadow-lg transition hover:scale-[1.02] disabled:opacity-60"
        >
          {syncing.all ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Master Sync Running...
            </>
          ) : (
            <>
              <Database size={16} />
              Master Sync
            </>
          )}
        </button>
      </div>
      
      {status.all.status !== "idle" && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 rounded-xl border border-white/10 bg-white/5 p-3"
        >
          <div className="flex items-center gap-2 text-sm">
            {status.all.status === "running" && <Loader2 size={14} className="animate-spin text-cyan-400" />}
            {status.all.status === "completed" && <CheckCircle size={14} className="text-emerald-400" />}
            {status.all.status === "failed" && <XCircle size={14} className="text-red-400" />}
            <span className="text-zinc-200">{status.all.message}</span>
          </div>
        </motion.div>
      )}
      
      <div className="mt-4 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
        {syncButtons.map(({ type, label, description }) => (
          <button
            key={type}
            onClick={() => triggerSync(type)}
            disabled={syncing[type]}
            className="relative overflow-hidden rounded-xl border border-white/10 bg-white/5 p-3 text-left transition hover:bg-white/10 disabled:opacity-60"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-zinc-100">{label}</span>
                  {syncing[type] && (
                    <Loader2 size={12} className="animate-spin text-cyan-400" />
                  )}
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">{description}</div>
              </div>
              
              {status[type].status !== "idle" && (
                <div>
                  {status[type].status === "running" && (
                    <div className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
                  )}
                  {status[type].status === "completed" && (
                    <CheckCircle size={14} className="text-emerald-400" />
                  )}
                  {status[type].status === "failed" && (
                    <XCircle size={14} className="text-red-400" />
                  )}
                </div>
              )}
            </div>
            
            {status[type].status === "running" && (
              <motion.div
                initial={{ width: "0%" }}
                animate={{ width: "100%" }}
                transition={{ duration: 30, ease: "linear" }}
                className="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-emerald-400 to-cyan-400"
              />
            )}
            
            {status[type].error && (
              <div className="mt-2 text-xs text-red-300">{status[type].error}</div>
            )}
          </button>
        ))}
      </div>
      
      <div className="mt-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-3 py-2 text-xs text-cyan-200">
        <div className="flex items-center gap-2">
          <RefreshCw size={12} />
          <span>Auto-sync runs daily at 2 AM. Enable in System Settings.</span>
        </div>
      </div>
    </div>
  );
}
