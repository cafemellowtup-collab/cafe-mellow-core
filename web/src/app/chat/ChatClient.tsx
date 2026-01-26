"use client";

import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Plus, Sparkles, Trash2, MapPin, Lightbulb } from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";
import SmartMarkdown from "@/components/SmartMarkdown";
import "highlight.js/styles/github-dark.css";

type Msg = {
  role: "user" | "assistant";
  content: string;
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

const STORAGE_KEY = "titan.chat.sessions.v2";
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
    "**TITAN CFO online.** I speak in numbers, root causes, and action items.\n\nUse the **CEO Command Chips** below or ask:\n- *\"Scan profit leaks for last 30 days\"*\n- *\"Why did expenses spike this week?\"*\n- *\"Cash position vs yesterday\"*",
};

const ceoCommandChips = [
  { label: "🔍 Scan Profit Leaks", prompt: "Scan all profit leaks in last 30 days with root causes and action items" },
  { label: "📊 Revenue vs Target", prompt: "Compare actual revenue vs target for this week with variance analysis" },
  { label: "⚠️ Wastage Alert", prompt: "Show top 5 wastage items by cost impact with immediate corrective actions" },
  { label: "💰 Cash Flow Status", prompt: "Cash flow status for today: inflows, outflows, and net position" },
  { label: "📈 Top Performers", prompt: "Top 10 best-selling items this week ranked by profit margin" },
  { label: "🚨 Expense Anomalies", prompt: "Detect expense anomalies and unauthorized spending in last 7 days" },
];

function makeNewSession(): ChatSession {
  const t = now();
  return {
    id: newId(),
    title: "New chat",
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

function LiveProcessingStatus() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start"
    >
      <div className="max-w-[85%] rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-900/20 to-cyan-900/20 px-4 py-3 text-sm shadow-lg">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-400/30 border-t-emerald-400" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-[10px] font-bold text-emerald-300">AI</span>
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-100">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
              TITAN CFO Processing
            </div>
            <div className="mt-0.5 text-[11px] text-zinc-400">
              Querying BigQuery → Analyzing data → Generating insights...
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function safeSaveSessions(sessions: ChatSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch {
    // ignore
  }
}

export default function ChatClient() {
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

  // Proactive Morning Briefing - Digital CEO Intelligence
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
        
        // Inject briefing as AI message in the active session
        upsertSession((s) => {
          const hasGreeting = s.messages.some(m => m.content.includes("Good morning"));
          if (hasGreeting) return s;
          
          const briefMsg: Msg = {
            role: "assistant",
            content: brief.summary || "Good morning. Digital CEO systems online.",
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
        // Silently fail - briefing is optional
      }
    }

    const timer = setTimeout(() => void fetchMorningBrief(), 800);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    if (!cleaned) return "New chat";
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
      const willTitle = s.title === "New chat";
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
    <div className="relative flex flex-col gap-4 xl:grid xl:grid-cols-[15rem_1fr_17rem] xl:gap-5">
      <aside className="hidden w-60 shrink-0 rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.1),_transparent_45%),_rgba(12,12,16,0.9)] p-4 backdrop-blur-xl xl:block">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[11px] uppercase tracking-[0.26em] text-emerald-200">Sessions</div>
            <div className="text-sm font-semibold text-white">Executive threads</div>
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

        <div className="mt-4 space-y-2">
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
                    <div className="truncate font-semibold text-white">{s.title || "New chat"}</div>
                    <div className="mt-0.5 truncate text-[11px] text-zinc-400">{s.messages.length} messages</div>
                  </div>

                  <span className="flex shrink-0 items-center gap-2">
                    <span
                      className={
                        "h-2 w-2 rounded-full transition " +
                        (active
                          ? "bg-emerald-400 shadow-[0_0_0_6px_rgba(16,185,129,0.22)]"
                          : "bg-zinc-700 group-hover:bg-emerald-300")
                      }
                    />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteChat(s.id);
                      }}
                      className="rounded-md border border-white/10 bg-white/5 p-1 text-zinc-300 transition hover:border-red-400/50 hover:text-red-100"
                      type="button"
                      aria-label="Delete chat"
                    >
                      <Trash2 size={14} />
                    </button>
                  </span>
                </motion.button>
              );
            })}
          </AnimatePresence>
        </div>
      </aside>

      <section className="min-w-0 overflow-hidden rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_20%_20%,rgba(52,211,153,0.08),transparent_35%),_rgba(10,10,12,0.9)] shadow-2xl shadow-emerald-500/10 backdrop-blur-xl">
        <div className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-3 border-b border-white/5 bg-black/40 px-4 py-3 backdrop-blur-sm lg:px-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.26em] text-emerald-200">Titan / CEO Chat</div>
            <div className="text-lg font-semibold text-white">Ultra-fast, premium responses.</div>
            <div className="text-xs text-zinc-400">Streaming SSE • Guardrailed BigQuery • CEO-grade reasoning</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowSessions(true)}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[12px] text-zinc-200 xl:hidden"
            >
              <Plus size={14} className="text-emerald-300" /> History
            </button>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[12px] text-zinc-200">
              <Sparkles size={14} className="text-emerald-300" /> {activeSession?.title ?? "New chat"}
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
                      {m.role === "user" ? "You" : "Titan"}
                      <span className="h-px w-6 bg-emerald-300/30" />
                    </div>
                    <SmartMarkdown content={m.content || ""} />
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            {loading ? <LiveProcessingStatus /> : null}
            <div ref={scrollRef} />
          </div>
        </div>

        <div className="border-t border-white/5 bg-black/50 p-4 lg:p-6">
          {error ? (
            <div className="mb-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-50">
              {error}
            </div>
          ) : null}

          <div className="mb-3">
            <div className="mb-1.5 text-[10px] uppercase tracking-[0.2em] text-zinc-500">CEO Command Chips</div>
            <div className="flex flex-wrap gap-2">
              {ceoCommandChips.map((chip) => (
                <motion.button
                  key={chip.label}
                  whileTap={{ scale: 0.95 }}
                  type="button"
                  onClick={() => void send(chip.prompt)}
                  className="rounded-xl border border-emerald-500/30 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 px-3 py-1.5 text-xs font-medium text-emerald-100 transition hover:border-emerald-400/50 hover:from-emerald-500/20 hover:to-cyan-500/20"
                >
                  {chip.label}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="flex w-full flex-col gap-3 lg:flex-row lg:items-center">
            <div className="flex w-full flex-1 items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 shadow-inner shadow-black/40">
              <div className="rounded-lg bg-emerald-500/20 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-emerald-100">
                Prompt
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
                placeholder="Ask Titan… e.g., 'Profit bridge for last 30 days and root cause'"
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
              <Send size={16} /> Send
            </motion.button>
          </div>

          <div className="mt-2 flex items-center justify-between text-[11px] text-zinc-500">
            <span>Titan works best with specifics: metric + period + desired outcome.</span>
            <motion.button
              whileTap={{ scale: 0.95 }}
              type="button"
              onClick={() => {
                const feedback = prompt("Suggest a feature or teach Titan a new rule:");
                if (feedback) {
                  void fetch(`${API_BASE_URL}${API_PREFIX}/metacognitive/learn`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      org_id: tenant.org_id,
                      location_id: tenant.location_id,
                      rule_type: "user_feedback",
                      description: feedback,
                      created_by: "user",
                    }),
                  }).then(() => alert("Feedback saved! Titan will learn from this."));
                }
              }}
              className="inline-flex items-center gap-1 rounded-lg border border-purple-400/30 bg-purple-500/10 px-2 py-1 text-xs text-purple-200 transition hover:border-purple-400/50 hover:bg-purple-500/15"
            >
              <Lightbulb size={12} /> Teach Titan
            </motion.button>
          </div>
        </div>
      </section>

      <AnimatePresence>
        {showSessions ? (
          <motion.aside
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            className="fixed inset-y-4 left-4 z-20 w-72 rounded-2xl border border-white/5 bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.1),_transparent_45%),_rgba(12,12,16,0.95)] p-4 shadow-2xl shadow-emerald-500/20 backdrop-blur-xl xl:hidden"
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[11px] uppercase tracking-[0.26em] text-emerald-200">Sessions</div>
                <div className="text-sm font-semibold text-white">Executive threads</div>
              </div>
              <button
                onClick={() => setShowSessions(false)}
                className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-zinc-200"
                type="button"
              >
                Close
              </button>
            </div>
            <div className="space-y-2 overflow-y-auto">
              {sessions.map((s) => {
                const active = s.id === activeId;
                return (
                  <button
                    key={s.id}
                    onClick={() => {
                      setActiveId(s.id);
                      setShowSessions(false);
                    }}
                    className="flex w-full items-center justify-between gap-3 rounded-xl border px-3 py-2 text-left text-sm transition"
                    style={{
                      borderColor: active ? "rgba(52,211,153,0.35)" : "rgba(255,255,255,0.06)",
                      background: active
                        ? "linear-gradient(120deg, rgba(52,211,153,0.18), rgba(34,211,238,0.15))"
                        : "rgba(255,255,255,0.04)",
                    }}
                  >
                    <div className="min-w-0">
                      <div className="truncate font-semibold text-white">{s.title || "New chat"}</div>
                      <div className="mt-0.5 truncate text-[11px] text-zinc-400">{s.messages.length} messages</div>
                    </div>
                    <span
                      className={
                        "h-2 w-2 rounded-full transition " +
                        (active
                          ? "bg-emerald-400 shadow-[0_0_0_6px_rgba(16,185,129,0.22)]"
                          : "bg-zinc-700")
                      }
                    />
                  </button>
                );
              })}
            </div>
          </motion.aside>
        ) : null}
      </AnimatePresence>

      <Suspense
        fallback={
          <aside className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <div>
                <div className="h-3 w-20 animate-pulse rounded bg-white/10" />
                <div className="mt-2 h-4 w-32 animate-pulse rounded bg-white/10" />
              </div>
              <span className="h-2 w-2 rounded-full bg-emerald-400/60" />
            </div>
            <div className="mt-4 space-y-3">
              {[1, 2, 3].map((k) => (
                <div key={k} className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <div className="h-3 w-24 animate-pulse rounded bg-white/10" />
                  <div className="mt-2 h-4 w-full animate-pulse rounded bg-white/10" />
                </div>
              ))}
            </div>
          </aside>
        }
      >
        <ContextPanel lastUserMsg={lastUserMsg} sources={activeSession?.sources} />
      </Suspense>
    </div>
  );
}
