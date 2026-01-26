"use client";

import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Plus, Sparkles, Trash2, TrendingUp, TrendingDown, Activity } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";
import SmartMarkdown from "@/components/SmartMarkdown";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import "highlight.js/styles/github-dark.css";

type Msg = {
  role: "user" | "assistant";
  content: string;
  status?: string;
  chart?: { type: "line" | "bar"; data: any[]; xKey: string; yKey: string; title: string };
};

type ChatSession = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Msg[];
  sources?: {
    time_window?: string;
    total_cost_inr?: number;
    queries?: Array<{ purpose?: string; bytes?: number; cost_inr?: number }>;
  };
};

const STORAGE_KEY = "titan.chat.sessions.v3";
const API_PREFIX = "/api/v1";

const ContextPanel = lazy(() => import("./ChatContextPanel"));

function now() {
  return Date.now();
}

function newId() {
  return `${now()}_${Math.random().toString(16).slice(2)}`;
}

const initialAssistantMsg: Msg = {
  role: "assistant",
  content:
    "I'm **TITAN CFO** — your ruthless financial intelligence. I speak only in hard numbers and actionable directives.\n\n**No generic advice. Only operational commands.**",
};

const ceoCommands = [
  "Generate Daily Brief",
  "Scan for Profit Leaks",
  "Top Revenue Drivers This Week",
  "Wastage Root Cause Analysis",
  "Cost Optimization Targets",
  "Staff Performance vs Revenue",
];

function makeNewSession(): ChatSession {
  const t = now();
  return {
    id: newId(),
    title: "New Executive Thread",
    createdAt: t,
    updatedAt: t,
    messages: [initialAssistantMsg],
  };
}

function safeLoadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as ChatSession[];
  } catch {
    return [];
  }
}

function LiveStatusIndicator({ status }: { status?: string }) {
  if (!status) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-100"
    >
      <Activity size={14} className="animate-pulse text-cyan-400" />
      <span className="font-mono">{status}</span>
    </motion.div>
  );
}

function TitanInnerMonologue({ loading }: { loading: boolean }) {
  const [status, setStatus] = useState("Initializing Titan Core...");

  useEffect(() => {
    if (!loading) return;
    
    const statuses = [
      "Scanning 45,000+ ledger rows...",
      "Cross-referencing sales vs inventory...",
      "Detecting anomalies and gaps...",
      "Computing profit bridges...",
      "Generating actionable directives...",
    ];
    
    let idx = 0;
    const interval = setInterval(() => {
      idx = (idx + 1) % statuses.length;
      setStatus(statuses[idx]!);
    }, 2000);
    
    return () => clearInterval(interval);
  }, [loading]);

  if (!loading) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start"
    >
      <div className="max-w-[80%] rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 px-4 py-3 text-sm text-cyan-100 shadow-lg">
        <div className="flex items-center gap-2">
          <Activity size={16} className="animate-pulse text-cyan-400" />
          <span className="font-mono text-xs">{status}</span>
        </div>
      </div>
    </motion.div>
  );
}

function InChatVisualization({ chart }: { chart: Msg["chart"] }) {
  if (!chart) return null;

  return (
    <div className="mt-4 rounded-xl border border-white/10 bg-black/40 p-4">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-200">
        {chart.title}
      </div>
      <ResponsiveContainer width="100%" height={200}>
        {chart.type === "line" ? (
          <LineChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={chart.xKey} stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
            <Line type="monotone" dataKey={chart.yKey} stroke="#34d399" strokeWidth={2} dot={{ fill: "#34d399" }} />
          </LineChart>
        ) : (
          <BarChart data={chart.data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey={chart.xKey} stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
            <Bar dataKey={chart.yKey} fill="#34d399" />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

function safeSaveSessions(sessions: ChatSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // ignore
  }
}

export default function ChatClientEnhanced() {
  const { tenant } = useTenant();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<string>("");
  const [input, setInput] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSessions, setShowSessions] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [briefingLoaded, setBriefingLoaded] = useState(false);

  useEffect(() => {
    const loaded = safeLoadSessions();
    if (loaded.length > 0) {
      loaded.sort((a, b) => b.updatedAt - a.updatedAt);
      setSessions(loaded);
      setActiveId(loaded[0]!.id);
      return;
    }
    const s = makeNewSession();
    setSessions([s]);
    setActiveId(s.id);
  }, []);

  useEffect(() => {
    if (briefingLoaded) return;

    const currentOrgId = tenant.org_id;
    const currentLocationId = tenant.location_id;

    async function fetchMorningBrief() {
      try {
        const params = new URLSearchParams({
          org_id: currentOrgId,
          location_id: currentLocationId,
        }).toString();
        
        const res = await fetch(`${API_BASE_URL}${API_PREFIX}/ceo/morning-brief?${params}`);
        if (!res.ok) return;
        
        const brief = await res.json();
        
        upsertSession((s) => {
          const hasGreeting = s.messages.some(m => m.content.includes("TITAN CFO"));
          if (hasGreeting) return s;
          
          const briefMsg: Msg = {
            role: "assistant",
            content: brief.summary || "Good morning. TITAN CFO systems online.",
          };
          
          return {
            ...s,
            updatedAt: now(),
            messages: [...s.messages, briefMsg],
          };
        });
        
        setBriefingLoaded(true);
        setTimeout(() => scrollRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
      } catch {
        // Silently fail
      }
    }

    const timer = setTimeout(() => void fetchMorningBrief(), 800);
    return () => clearTimeout(timer);
  }, [tenant.org_id, tenant.location_id]);

  useEffect(() => {
    if (!sessions.length) return;
    safeSaveSessions(sessions);
  }, [sessions]);

  const activeSession = useMemo(() => {
    return sessions.find((s) => s.id === activeId) ?? null;
  }, [sessions, activeId]);

  const messages = activeSession?.messages ?? [];

  const lastUserMsg = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i]?.role === "user") return messages[i]?.content ?? "";
    }
    return "";
  }, [messages]);

  function upsertSession(patch: (s: ChatSession) => ChatSession) {
    setSessions((prev) =>
      prev
        .map((s) => (s.id === activeId ? patch(s) : s))
        .sort((a, b) => b.updatedAt - a.updatedAt)
    );
  }

  function newChat() {
    const s = makeNewSession();
    setSessions((prev) => [s, ...prev]);
    setActiveId(s.id);
    setError(null);
    setInput("");
    setTimeout(() => scrollRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  }

  function deleteChat(id: string) {
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== id);
      if (id === activeId) {
        const next = [...remaining].sort((a, b) => b.updatedAt - a.updatedAt)[0];
        if (next) {
          setActiveId(next.id);
          return remaining;
        }
        const s = makeNewSession();
        setActiveId(s.id);
        return [s];
      }
      return remaining;
    });
  }

  function autoTitleFrom(text: string) {
    const cleaned = text.replace(/\s+/g, " ").trim();
    if (!cleaned) return "New Executive Thread";
    return cleaned.length > 42 ? cleaned.slice(0, 42) + "…" : cleaned;
  }

  function appendToLastAssistant(text: string) {
    if (!text) return;
    upsertSession((s) => {
      const next = [...s.messages];
      for (let i = next.length - 1; i >= 0; i--) {
        if (next[i]?.role === "assistant") {
          next[i] = { ...next[i], content: (next[i]?.content ?? "") + text };
          return { ...s, updatedAt: now(), messages: next };
        }
      }
      return { ...s, updatedAt: now(), messages: [...next, { role: "assistant", content: text }] };
    });
  }

  async function send(prompt?: string) {
    const text = (prompt ?? input).trim();
    if (!text || loading) return;
    if (!activeSession) return;

    setError(null);
    setLoading(true);
    setInput("");

    upsertSession((s) => {
      const willTitle = s.title === "New Executive Thread";
      const title = willTitle ? autoTitleFrom(text) : s.title;
      return {
        ...s,
        title,
        updatedAt: now(),
        messages: [...s.messages, { role: "user", content: text }, { role: "assistant", content: "" }],
      };
    });

    try {
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: text,
          org_id: tenant.org_id,
          location_id: tenant.location_id,
        }),
      });

      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as unknown;
        const msg =
          data && typeof data === "object" && "detail" in data
            ? String((data as { detail?: unknown }).detail)
            : `Request failed (${res.status})`;
        throw new Error(msg);
      }

      if (!res.body) {
        throw new Error("Streaming not supported by browser/response");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buf = "";
      let done = false;

      while (!done) {
        const r = await reader.read();
        done = r.done;
        buf += decoder.decode(r.value ?? new Uint8Array(), { stream: !done });

        let sepIdx = buf.indexOf("\n\n");
        while (sepIdx !== -1) {
          const rawEvent = buf.slice(0, sepIdx);
          buf = buf.slice(sepIdx + 2);

          let eventType: string | null = null;
          const dataLines: string[] = [];
          for (const line of rawEvent.split("\n")) {
            if (line.startsWith("event:")) eventType = line.slice(6).trim();
            if (line.startsWith("data: ")) dataLines.push(line.slice(6));
            else if (line.startsWith("data:")) dataLines.push(line.slice(5));
          }

          const payload = dataLines.join("\n");
          if (eventType === "error") {
            throw new Error(payload || "Stream error");
          }
          if (eventType === "sources") {
            try {
              const parsed = JSON.parse(payload);
              upsertSession((s) => ({ ...s, updatedAt: now(), sources: parsed }));
            } catch {
              // ignore
            }
            sepIdx = buf.indexOf("\n\n");
            continue;
          }
          if (eventType === "done") {
            done = true;
            break;
          }

          appendToLastAssistant(payload.replace(/\\n/g, "\n"));
          setTimeout(() => scrollRef.current?.scrollIntoView({ behavior: "smooth" }), 12);

          sepIdx = buf.indexOf("\n\n");
        }
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex flex-col gap-4 xl:grid xl:grid-cols-[20%_80%] xl:gap-5">
      <aside className="hidden w-full shrink-0 rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.1),_transparent_45%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl xl:block">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.26em] text-emerald-200">History</div>
            <div className="text-sm font-semibold text-white">Executive Threads</div>
          </div>
          <motion.button
            whileTap={{ scale: 0.96 }}
            onClick={() => newChat()}
            className="inline-flex items-center gap-1 rounded-lg bg-gradient-to-r from-emerald-400 to-cyan-400 px-3 py-1.5 text-[12px] font-semibold text-black shadow-lg shadow-emerald-500/30 transition hover:scale-[1.02]"
            type="button"
          >
            <Plus size={14} /> New
          </motion.button>
        </div>

        <div className="mt-4 space-y-2 overflow-y-auto" style={{ maxHeight: "calc(100vh - 200px)" }}>
          <AnimatePresence initial={false}>
            {sessions.map((s) => {
              const active = s.id === activeId;
              return (
                <motion.button
                  layout
                  key={s.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  onClick={() => setActiveId(s.id)}
                  className="group flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left text-sm transition"
                  style={{
                    borderColor: active ? "rgba(52,211,153,0.35)" : "rgba(255,255,255,0.06)",
                    background: active
                      ? "linear-gradient(120deg, rgba(52,211,153,0.18), rgba(34,211,238,0.15))"
                      : "rgba(255,255,255,0.04)",
                  }}
                >
                  <div className="min-w-0">
                    <div className="truncate font-semibold text-white">{s.title || "New Thread"}</div>
                    <div className="mt-0.5 truncate text-[11px] text-zinc-400">{s.messages.length} msgs</div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChat(s.id);
                    }}
                    className="rounded-md border border-white/10 bg-white/5 p-1 text-zinc-300 transition hover:border-red-400/50 hover:text-red-100"
                    type="button"
                    aria-label="Delete thread"
                  >
                    <Trash2 size={14} />
                  </button>
                </motion.button>
              );
            })}
          </AnimatePresence>
        </div>
      </aside>

      <section className="min-w-0 overflow-hidden rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_20%_20%,rgba(52,211,153,0.08),transparent_35%),_rgba(10,10,12,0.9)] shadow-2xl shadow-emerald-500/10 backdrop-blur-xl">
        <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-white/5 bg-black/40 px-4 py-3 backdrop-blur-sm lg:px-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.26em] text-emerald-200">Titan / CFO Command Center</div>
            <div className="text-lg font-semibold text-white">Enterprise Intelligence • 45s Timeout</div>
            <div className="text-xs text-zinc-400">Only hard numbers. Only actionable directives.</div>
          </div>
          <div className="flex items-center gap-2">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[12px] text-zinc-200">
              <Sparkles size={14} className="text-emerald-300" /> {activeSession?.title ?? "New Thread"}
            </div>
          </div>
        </div>

        <div className="h-[68vh] overflow-auto px-4 py-4 lg:px-6">
          <div className="space-y-4">
            <AnimatePresence initial={false}>
              {messages.map((m, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.18, ease: "easeOut" }}
                  className={"flex " + (m.role === "user" ? "justify-end" : "justify-start")}
                >
                  <div
                    className={
                      "group max-w-[85%] rounded-2xl border px-4 py-3 text-sm leading-6 shadow-lg transition " +
                      (m.role === "user"
                        ? "border-emerald-500/30 bg-gradient-to-br from-emerald-600/15 to-cyan-500/15 text-emerald-50"
                        : "border-white/10 bg-white/5 text-white/90")
                    }
                  >
                    <div className="mb-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-emerald-200/80">
                      {m.role === "user" ? "CEO" : "Titan CFO"}
                      <span className="h-px w-6 bg-emerald-300/30" />
                    </div>
                    <SmartMarkdown content={m.content || ""} />
                    {m.chart && <InChatVisualization chart={m.chart} />}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {loading ? <TitanInnerMonologue loading={loading} /> : null}
            <div ref={scrollRef} />
          </div>
        </div>

        <div className="border-t border-white/5 bg-black/50 p-4 lg:p-6">
          {error ? (
            <div className="mb-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-50">
              {error}
            </div>
          ) : null}

          <div className="mb-3 flex flex-wrap gap-2 text-xs text-zinc-400">
            {ceoCommands.map((cmd) => (
              <motion.button
                key={cmd}
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={() => void send(cmd)}
                disabled={loading}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 transition hover:border-emerald-400/40 hover:bg-emerald-500/10 hover:text-emerald-50 disabled:opacity-50"
              >
                {cmd}
              </motion.button>
            ))}
          </div>

          <div className="flex w-full flex-col gap-3 lg:flex-row lg:items-center">
            <div className="flex w-full flex-1 items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 shadow-inner shadow-black/40">
              <div className="rounded-lg bg-emerald-500/20 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-100">
                CEO
              </div>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void send();
                  }
                }}
                placeholder="Issue directive... e.g., 'Maida wastage root cause and action plan'"
                className="min-w-0 flex-1 bg-transparent text-sm text-zinc-50 placeholder:text-zinc-500 outline-none"
              />
            </div>
            <motion.button
              whileTap={{ scale: 0.97 }}
              onClick={() => void send()}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-400 to-cyan-400 px-6 py-3 text-sm font-semibold text-black shadow-lg shadow-emerald-500/30 transition hover:scale-[1.01] disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              <Send size={16} /> Execute
            </motion.button>
          </div>

          <div className="mt-2 flex items-center justify-between text-[10px] text-zinc-500">
            <span>Titan CFO: No fluff. Pure intelligence. 45-second deep analysis.</span>
          </div>
        </div>
      </section>
    </div>
  );
}
