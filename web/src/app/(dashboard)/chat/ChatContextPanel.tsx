"use client";

import type { ReactNode } from "react";

export type ChatSources = {
  time_window?: string;
  total_cost_inr?: number;
  queries?: Array<{ purpose?: string; bytes?: number; cost_inr?: number }>;
};

export default function ChatContextPanel({
  lastUserMsg,
  sources,
}: {
  lastUserMsg: string;
  sources?: ChatSources;
}) {
  const queries = sources?.queries ?? [];
  return (
    <aside className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-emerald-200">Context</div>
          <div className="text-sm font-semibold text-white">Sources & signals</div>
        </div>
        <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_0_6px_rgba(52,211,153,0.15)]" />
      </div>

      <div className="mt-4 space-y-3">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="text-xs text-zinc-400">Last user message</div>
          <div className="mt-1 text-sm font-medium text-white/90">{lastUserMsg || "—"}</div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center justify-between text-xs text-zinc-400">
            <span>Queries & cost</span>
            <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[11px] font-medium text-emerald-200 ring-1 ring-emerald-400/30">
              Beta
            </span>
          </div>
          <div className="mt-2 text-sm text-zinc-200">
            {sources?.time_window ? (
              <div className="text-xs text-zinc-400">Time window: {sources.time_window}</div>
            ) : (
              <div className="text-xs text-zinc-500">Time window: —</div>
            )}
            <div className="mt-1 text-xs text-zinc-400">
              Total est. cost: ₹
              {typeof sources?.total_cost_inr === "number" ? sources.total_cost_inr.toFixed(2) : "0.00"}
            </div>
          </div>

          <div className="mt-3 space-y-2">
            {queries.length ? (
              queries.slice(0, 8).map((q, i) => (
                <div key={i} className="rounded-lg border border-white/10 bg-white/5 px-2 py-2">
                  <div className="text-xs font-medium text-white/90">{q.purpose || "(unknown)"}</div>
                  <div className="mt-0.5 text-[11px] text-zinc-400">
                    ₹{typeof q.cost_inr === "number" ? q.cost_inr.toFixed(2) : "0.00"}
                    {typeof q.bytes === "number" ? ` • ${Math.round(q.bytes / (1024 * 1024))} MB` : ""}
                  </div>
                </div>
              ))
            ) : (
              <div className="mt-2 text-xs text-zinc-500">No query metadata captured yet.</div>
            )}
          </div>
        </div>

        <UpgradesCard>
          <div className="text-xs uppercase tracking-[0.18em] text-emerald-200/80">Upgrades</div>
          <ul className="mt-2 space-y-1 text-sm text-zinc-200">
            <li>• Streaming responses</li>
            <li>• Persisted sessions</li>
            <li>• BigQuery cost + citations</li>
            <li>• CEO agent tools (sales / expenses / wastage)</li>
          </ul>
        </UpgradesCard>
      </div>
    </aside>
  );
}

function UpgradesCard({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      {children}
    </div>
  );
}
