"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Activity, Database, Zap } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";

const API_PREFIX = "/api/v1";

type Overview = {
  ok: boolean;
  start: string;
  end: string;
  days: number;
  revenue: number;
  expenses: number;
  net: number;
  avg_daily_revenue: number;
};

type RevExpSeries = {
  ok: boolean;
  start: string;
  end: string;
  dates: string[];
  revenue: number[];
  expenses: number[];
  net: number[];
};

type TaskItem = {
  created_at?: string;
  task_type?: string;
  item_involved?: string;
  description?: string;
  priority?: string;
  department?: string;
  status?: string;
};

type TasksResp = { ok: boolean; items: TaskItem[] };

type DataQualityScore = {
  score: number;
  tier: "RED" | "YELLOW" | "GREEN";
  dimensions: {
    completeness: number;
    freshness: number;
    consistency: number;
    accuracy: number;
  };
  recommendations: string[];
};

function fmtINR(n: number) {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(n || 0);
  } catch {
    return `₹${Math.round(n || 0)}`;
  }
}

function toISO(d: Date) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function daysAgo(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

function RadialGauge({ score, tier }: { score: number; tier: string }) {
  const radius = 70;
  const strokeWidth = 12;
  const normalizedRadius = radius - strokeWidth / 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  
  const safeScore = (typeof score === 'number' && !isNaN(score) && isFinite(score)) ? score : 50;
  const strokeDashoffset = circumference - (safeScore / 100) * circumference;

  const tierColors = {
    GREEN: { stroke: "#10b981", glow: "rgba(16, 185, 129, 0.3)" },
    YELLOW: { stroke: "#f59e0b", glow: "rgba(245, 158, 11, 0.3)" },
    RED: { stroke: "#ef4444", glow: "rgba(239, 68, 68, 0.3)" },
  };

  const safeTier = tier?.toUpperCase() || "YELLOW";
  const colors = tierColors[safeTier as keyof typeof tierColors] || tierColors.YELLOW;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2}>
        <circle
          stroke="#27272a"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={colors.stroke}
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference + " " + circumference}
          style={{ strokeDashoffset, transition: "stroke-dashoffset 0.6s ease" }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          transform={`rotate(-90 ${radius} ${radius})`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-3xl font-bold text-white">{Math.round(safeScore)}</div>
        <div className="text-[10px] uppercase tracking-wider text-zinc-400">Quality</div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/5 p-4 backdrop-blur-xl">
      <div className="h-3 w-20 animate-pulse rounded bg-white/10" />
      <div className="mt-2 h-8 w-32 animate-pulse rounded bg-white/10" />
      <div className="mt-2 h-3 w-24 animate-pulse rounded bg-white/10" />
    </div>
  );
}

function SimpleLineChart({
  dates,
  revenue,
  expenses,
}: {
  dates: string[];
  revenue: number[];
  expenses: number[];
}) {
  const w = 640;
  const h = 220;
  const pad = 16;

  const n = Math.max(0, dates.length);
  const xs = useMemo(() => {
    if (n <= 1) return [pad];
    const span = w - pad * 2;
    return Array.from({ length: n }, (_, i) => pad + (span * i) / (n - 1));
  }, [n]);

  const maxY = useMemo(() => {
    const all = [...(revenue ?? []), ...(expenses ?? [])].filter((x) => Number.isFinite(x));
    return all.length ? Math.max(...all) : 1;
  }, [revenue, expenses]);

  const minY = useMemo(() => {
    const all = [...(revenue ?? []), ...(expenses ?? [])].filter((x) => Number.isFinite(x));
    return all.length ? Math.min(...all) : 0;
  }, [revenue, expenses]);

  const yFor = (v: number) => {
    const span = Math.max(1, maxY - minY);
    const t = (v - minY) / span;
    return h - pad - t * (h - pad * 2);
  };

  const pathFor = (arr: number[]) => {
    if (!arr || !arr.length) return "";
    return arr.map((v, i) => `${xs[i] ?? pad},${yFor(v)}`).join(" ");
  };

  const revPts = pathFor(revenue);
  const expPts = pathFor(expenses);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_bottom_right,_rgba(52,211,153,0.08),_transparent_40%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-white">Revenue vs Expenses</div>
          <div className="mt-1 text-xs text-zinc-400">
            Daily totals for the selected period
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-2 text-emerald-200">
            <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" /> Revenue
          </div>
          <div className="flex items-center gap-2 text-rose-200">
            <span className="h-2 w-2 rounded-full bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.6)]" /> Expenses
          </div>
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <svg width={w} height={h} className="block">
          <line x1={pad} y1={pad} x2={pad} y2={h - pad} stroke="#27272a" />
          <line x1={pad} y1={h - pad} x2={w - pad} y2={h - pad} stroke="#27272a" />

          {revPts ? (
            <polyline
              fill="none"
              stroke="#34d399"
              strokeWidth="2"
              points={revPts}
            />
          ) : null}
          {expPts ? (
            <polyline
              fill="none"
              stroke="#fb7185"
              strokeWidth="2"
              points={expPts}
            />
          ) : null}
        </svg>
      </div>

      <div className="mt-3 flex items-center gap-2 rounded-lg border border-white/5 bg-white/5 px-3 py-2 text-[11px] text-zinc-400">
        <Zap size={12} className="text-emerald-300" />
        Tip: Use 60d/180d for smoother trends.
      </div>
    </motion.div>
  );
}

export default function DashboardClient() {
  const { tenant } = useTenant();
  const [start, setStart] = useState<string>(toISO(daysAgo(30)));
  const [end, setEnd] = useState<string>(toISO(new Date()));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [overview, setOverview] = useState<Overview | null>(null);
  const [series, setSeries] = useState<RevExpSeries | null>(null);
  const [tasks, setTasks] = useState<TasksResp | null>(null);
  const [dataQuality, setDataQuality] = useState<DataQualityScore | null>(null);

  const presets = useMemo(
    () => [
      { label: "7D", days: 7 },
      { label: "30D", days: 30 },
      { label: "60D", days: 60 },
      { label: "180D", days: 180 },
    ],
    []
  );

  async function fetchAll(s: string, e: string) {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ start: s, end: e }).toString();
      const dqParams = new URLSearchParams({
        org_id: tenant.org_id,
        location_id: tenant.location_id,
        days: "30",
      }).toString();
      
      const [o, se, t, dq] = await Promise.all([
        fetch(`${API_BASE_URL}/metrics/overview?${qs}`).then((r) => r.json()),
        fetch(`${API_BASE_URL}/metrics/revenue-expenses?${qs}`).then((r) => r.json()),
        fetch(`${API_BASE_URL}/tasks/pending?limit=20`).then((r) => r.json()),
        fetch(`${API_BASE_URL}${API_PREFIX}/analytics/data_quality?${dqParams}`).then((r) => r.json()).catch(() => null),
      ]);

      if (!o?.ok) throw new Error(o?.detail ?? "Failed to load overview");
      if (!se?.ok) throw new Error(se?.detail ?? "Failed to load chart");
      if (!t?.ok) throw new Error(t?.detail ?? "Failed to load tasks");

      setOverview(o as Overview);
      setSeries(se as RevExpSeries);
      setTasks(t as TasksResp);
      if (dq) setDataQuality(dq as DataQualityScore);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchAll(start, end);
  }, [tenant.org_id, tenant.location_id]);

  function applyPreset(days: number) {
    const e = new Date();
    const s = new Date();
    s.setDate(e.getDate() - days);
    const sIso = toISO(s);
    const eIso = toISO(e);
    setStart(sIso);
    setEnd(eIso);
    void fetchAll(sIso, eIso);
  }

  function applyCustom() {
    void fetchAll(start, end);
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-zinc-100">Date range</div>
            <div className="mt-1 text-xs text-zinc-500">
              Choose presets or set a custom period.
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {presets.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => applyPreset(p.days)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900"
                disabled={loading}
              >
                {p.label}
              </button>
            ))}

            <div className="mx-2 hidden h-6 w-px bg-zinc-800 md:block" />

            <div className="flex items-center gap-2">
              <input
                type="date"
                value={start}
                onChange={(e) => setStart(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
              />
              <span className="text-xs text-zinc-500">to</span>
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
              />
              <button
                type="button"
                onClick={() => applyCustom()}
                className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950 hover:bg-emerald-300 disabled:opacity-60"
                disabled={loading}
              >
                Apply
              </button>
            </div>
          </div>
        </div>

        {error ? (
          <div className="mt-3 rounded-xl border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs text-red-200">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="mt-3 text-xs text-zinc-500">Loading…</div>
        ) : null}
      </div>

      {loading ? (
        <div className="grid gap-4 lg:grid-cols-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(52,211,153,0.15),_transparent_50%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 text-xs text-emerald-200">
              <TrendingUp size={14} /> Revenue
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              {fmtINR(overview?.revenue ?? 0)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              Avg/day: {fmtINR(overview?.avg_daily_revenue ?? 0)}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(239,68,68,0.12),_transparent_50%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 text-xs text-rose-200">
              <TrendingDown size={14} /> Expenses
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              {fmtINR(overview?.expenses ?? 0)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">Period: {overview?.days ?? 0} days</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.12),_transparent_50%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 text-xs text-cyan-200">
              <Activity size={14} /> Net Profit
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              {fmtINR(overview?.net ?? 0)}
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              {((overview?.net ?? 0) / Math.max(1, overview?.revenue ?? 1) * 100).toFixed(1)}% margin
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.12),_transparent_50%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 text-xs text-amber-200">
              <Database size={14} /> Data Quality
            </div>
            {dataQuality && typeof dataQuality.score === 'number' && !isNaN(dataQuality.score) ? (
              <div className="mt-2 flex items-center gap-3">
                <RadialGauge score={dataQuality.score} tier={dataQuality.tier || "YELLOW"} />
                <div className="flex-1">
                  <div className="text-xs font-semibold text-white">{(dataQuality.tier || "YELLOW").toUpperCase()} Tier</div>
                  <div className="mt-1 text-[10px] text-zinc-400">
                    Chameleon Brain Active
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-2 flex items-center gap-3">
                <RadialGauge score={50} tier="YELLOW" />
                <div className="flex-1">
                  <div className="text-xs font-semibold text-white">YELLOW Tier</div>
                  <div className="mt-1 text-[10px] text-zinc-400">
                    Calculating...
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div>
          <SimpleLineChart
            dates={series?.dates ?? []}
            revenue={series?.revenue ?? []}
            expenses={series?.expenses ?? []}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top_right,_rgba(139,92,246,0.08),_transparent_40%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl"
        >
          <div className="text-sm font-semibold text-white">Pending tasks</div>
          <div className="mt-1 text-xs text-zinc-400">From ai_task_queue</div>

          <div className="mt-4 space-y-2">
            {(tasks?.items ?? []).length ? (
              (tasks?.items ?? []).slice(0, 12).map((t, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.7 + i * 0.05 }}
                  className="rounded-xl border border-white/5 bg-white/5 p-3 backdrop-blur-sm transition hover:border-white/10 hover:bg-white/10"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0 text-xs font-semibold text-white">
                      {(t.task_type || "Task") + (t.item_involved ? ` • ${t.item_involved}` : "")}
                    </div>
                    <div className="shrink-0 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-200">
                      {t.priority || "—"}
                    </div>
                  </div>
                  <div className="mt-1 line-clamp-3 text-xs text-zinc-400">
                    {t.description || "—"}
                  </div>
                </motion.div>
              ))
            ) : (
              <div className="text-xs text-zinc-400">No pending tasks.</div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
