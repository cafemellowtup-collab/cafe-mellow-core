"use client";

import { useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

type FiltersResp = {
  ok: boolean;
  ledgers: string[];
  main_categories: string[];
  categories: string[];
  employees?: string[];
  paid_froms?: string[];
  has_employee?: boolean;
  has_paid_from?: boolean;
};

type ExpenseRow = {
  expense_date: string;
  item_name: string;
  amount: number;
  category: string;
  ledger_name: string;
  main_category: string;
  paid_from: string;
  employee_name: string;
};

type ExpensesResp = {
  ok: boolean;
  start: string;
  end: string;
  filters: {
    ledger: string;
    main_category: string;
    employee?: string;
    paid_from?: string;
    q: string;
    min_amount: number | null;
    max_amount: number | null;
  };
  summary: { total_amount: number; row_count: number };
  items: ExpenseRow[];
};

type SalesFiltersResp = {
  ok: boolean;
  table: string;
  has_order_type: boolean;
  has_delivery_partner: boolean;
  has_payment_mode: boolean;
  order_types: string[];
  delivery_partners: string[];
  payment_modes: string[];
};

type SalesChannelRow = {
  channel: string;
  revenue: number;
  orders: number;
  line_items: number;
};

type SalesChannelsResp = {
  ok: boolean;
  table: string;
  start: string;
  end: string;
  order_types: SalesChannelRow[];
  delivery_partners: SalesChannelRow[];
};

type TopItemRow = {
  item_name: string;
  qty: number;
  revenue: number;
};

type TopItemsResp = {
  ok: boolean;
  table: string;
  start: string;
  end: string;
  filters: {
    order_type: string;
    delivery_partner: string;
  };
  items: TopItemRow[];
};

type OpsBriefKpis = {
  revenue?: number;
  expenses?: number;
  net?: number;
  orders?: number;
};

type OpsBriefTopItem = {
  item_name?: string;
  revenue?: number;
  qty?: number;
};

type OpsBriefAlert = {
  title?: string;
  message?: string;
  severity?: string;
  task_type?: string;
};

type OpsBriefDataFreshness = {
  latest_sales_date?: string;
  latest_expenses_date?: string;
};

type OpsBriefDeltaPct = {
  revenue?: number | null;
  expenses?: number | null;
  net?: number | null;
  orders?: number | null;
};

type OpsBriefComparisons = {
  last_week_same_day?: {
    delta_pct?: OpsBriefDeltaPct;
  };
};

type OpsBriefResp = {
  ok?: boolean;
  brief_date?: string;
  kpis?: OpsBriefKpis;
  comparisons?: OpsBriefComparisons;
  data_freshness?: OpsBriefDataFreshness;
  top_items_7d?: OpsBriefTopItem[];
  top_items?: OpsBriefTopItem[];
  alerts?: OpsBriefAlert[];
  insights?: string[];
};

function asArray(v: unknown): unknown[] {
  return Array.isArray(v) ? v : [];
}

function asString(v: unknown): string {
  return typeof v === "string" ? v : "";
}

function asNumber(v: unknown): number | undefined {
  return typeof v === "number" && Number.isFinite(v) ? v : undefined;
}

function asNullableNumber(v: unknown): number | null | undefined {
  if (v === null) return null;
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return undefined;
}

function parseOpsBrief(input: unknown): OpsBriefResp | null {
  if (!input || typeof input !== "object") return null;
  const o = input as Record<string, unknown>;

  const k = (o.kpis && typeof o.kpis === "object" ? (o.kpis as Record<string, unknown>) : null) ?? null;
  const kpis: OpsBriefKpis | undefined = k
    ? {
        revenue: asNumber(k.revenue),
        expenses: asNumber(k.expenses),
        net: asNumber(k.net),
        orders: asNumber(k.orders),
      }
    : undefined;

  const topItemsRaw = asArray(o.top_items_7d).length ? o.top_items_7d : o.top_items;
  const top_items_7d = asArray(topItemsRaw)
    .map((x) => {
      if (!x || typeof x !== "object") return null;
      const r = x as Record<string, unknown>;
      return {
        item_name: asString(r.item_name),
        revenue: asNumber(r.revenue),
        qty: asNumber(r.qty),
      } as OpsBriefTopItem;
    })
    .filter((x): x is OpsBriefTopItem => Boolean(x));

  const alerts = asArray(o.alerts)
    .map((x) => {
      if (!x || typeof x !== "object") return null;
      const r = x as Record<string, unknown>;
      return {
        title: asString(r.title),
        message: asString(r.message),
        severity: asString(r.severity),
        task_type: asString(r.task_type),
      } as OpsBriefAlert;
    })
    .filter((x): x is OpsBriefAlert => Boolean(x));

  const insightsRaw = o.insights;
  const insights: string[] =
    typeof insightsRaw === "string"
      ? [insightsRaw].filter(Boolean)
      : Array.isArray(insightsRaw)
        ? insightsRaw.map(asString).filter(Boolean)
        : [];

  const comparisonsRaw = o.comparisons && typeof o.comparisons === "object" ? (o.comparisons as Record<string, unknown>) : null;
  const lastWeekRaw =
    comparisonsRaw && comparisonsRaw.last_week_same_day && typeof comparisonsRaw.last_week_same_day === "object"
      ? (comparisonsRaw.last_week_same_day as Record<string, unknown>)
      : null;
  const deltaRaw = lastWeekRaw && lastWeekRaw.delta_pct && typeof lastWeekRaw.delta_pct === "object" ? (lastWeekRaw.delta_pct as Record<string, unknown>) : null;
  const comparisons: OpsBriefComparisons | undefined = deltaRaw
    ? {
        last_week_same_day: {
          delta_pct: {
            revenue: asNullableNumber(deltaRaw.revenue) ?? undefined,
            expenses: asNullableNumber(deltaRaw.expenses) ?? undefined,
            net: asNullableNumber(deltaRaw.net) ?? undefined,
            orders: asNullableNumber(deltaRaw.orders) ?? undefined,
          },
        },
      }
    : undefined;

  const freshnessRaw = o.data_freshness && typeof o.data_freshness === "object" ? (o.data_freshness as Record<string, unknown>) : null;
  const data_freshness: OpsBriefDataFreshness | undefined = freshnessRaw
    ? {
        latest_sales_date: asString(freshnessRaw.latest_sales_date) || undefined,
        latest_expenses_date: asString(freshnessRaw.latest_expenses_date) || undefined,
      }
    : undefined;

  return {
    ok: typeof o.ok === "boolean" ? o.ok : undefined,
    brief_date: asString(o.brief_date) || undefined,
    kpis,
    comparisons,
    data_freshness,
    top_items_7d,
    alerts,
    insights,
  };
}

function parseRecentBriefs(input: unknown): OpsBriefResp[] {
  if (!input || typeof input !== "object") return [];
  const o = input as Record<string, unknown>;
  const items = asArray(o.items);
  const parsed = items
    .map((x) => parseOpsBrief(x))
    .filter((x): x is OpsBriefResp => Boolean(x));
  return parsed;
}

async function sleep(ms: number) {
  await new Promise((r) => setTimeout(r, ms));
}

async function fetchJsonWithRetry<T>(url: string, init?: RequestInit, retries = 2): Promise<T> {
  let lastErr: unknown = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, init);
      const j = (await res.json().catch(() => null)) as unknown;
      if (!res.ok) {
        const detail = typeof j === "object" && j !== null && "detail" in j ? (j as { detail?: unknown }).detail : undefined;
        throw new Error(detail ? String(detail) : `HTTP ${res.status}`);
      }
      return j as T;
    } catch (e: unknown) {
      lastErr = e;
      if (attempt < retries) await sleep(350 * Math.pow(2, attempt));
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error(String(lastErr ?? "Request failed"));
}

function friendlyErrorMessage(err: unknown) {
  const raw = err instanceof Error ? err.message : String(err ?? "");
  const cleaned = raw.trim();
  if (!cleaned) return "Request failed. Please try again.";
  if (!raw) return "Request failed. Please try again.";
  // Hide BigQuery job IDs / noisy traces while keeping meaning.
  const cutMarkers = [" Location:", " Job ID:", " reason:", " Traceback", " at ["];
  let s = cleaned;
  for (const m of cutMarkers) {
    const idx = s.indexOf(m);
    if (idx > 0) s = s.slice(0, idx);
  }
  s = s.replace(/^400\s+/i, "").replace(/^500\s+/i, "").trim();
  if (s.length > 180) s = s.slice(0, 180).trimEnd() + "…";
  return s;
}

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

function toDateValue(iso: string | undefined): number | null {
  if (!iso) return null;
  // Expect YYYY-MM-DD. Keep this strict to avoid TZ surprises.
  if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null;
  const v = Date.parse(`${iso}T00:00:00Z`);
  return Number.isFinite(v) ? v : null;
}

function daysAgo(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

function safeSlug(s: string) {
  return s
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+/, "")
    .replace(/-+$/, "")
    .slice(0, 60);
}

function downloadCsv(filename: string, rows: Array<Record<string, unknown>>) {
  const cols = Array.from(
    rows.reduce<Set<string>>((s, r) => {
      Object.keys(r).forEach((k) => s.add(k));
      return s;
    }, new Set<string>())
  );

  const esc = (v: unknown) => {
    const s = v === null || v === undefined ? "" : String(v);
    if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };

  const head = cols.map(esc).join(",");
  const lines = rows.map((r) => cols.map((c) => esc(r[c])).join(","));
  const csv = [head, ...lines].join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function OperationsClient() {
  const [activeTab, setActiveTab] = useState<"expenses" | "sales">("expenses");
  const [start, setStart] = useState<string>(toISO(daysAgo(30)));
  const [end, setEnd] = useState<string>(toISO(new Date()));

  const [salesStart, setSalesStart] = useState<string>(toISO(daysAgo(30)));
  const [salesEnd, setSalesEnd] = useState<string>(toISO(new Date()));

  const [ledger, setLedger] = useState<string>("");
  const [mainCategory, setMainCategory] = useState<string>("");
  const [employee, setEmployee] = useState<string>("");
  const [paidFrom, setPaidFrom] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [minAmount, setMinAmount] = useState<string>("");
  const [maxAmount, setMaxAmount] = useState<string>("");
  const [limit, setLimit] = useState<number>(200);

  const [filters, setFilters] = useState<FiltersResp | null>(null);
  const [data, setData] = useState<ExpensesResp | null>(null);
  const [salesFilters, setSalesFilters] = useState<SalesFiltersResp | null>(null);
  const [salesChannels, setSalesChannels] = useState<SalesChannelsResp | null>(null);
  const [topItems, setTopItems] = useState<TopItemsResp | null>(null);
  const [salesOrderType, setSalesOrderType] = useState<string>("");
  const [salesDeliveryPartner, setSalesDeliveryPartner] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [salesLoading, setSalesLoading] = useState(false);
  const [salesError, setSalesError] = useState<string | null>(null);

  const [briefLoading, setBriefLoading] = useState(false);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [brief, setBrief] = useState<OpsBriefResp | null>(null);

  const [recentLoading, setRecentLoading] = useState(false);
  const [recentError, setRecentError] = useState<string | null>(null);
  const [recentBriefs, setRecentBriefs] = useState<OpsBriefResp[]>([]);

  const presets = useMemo(
    () => [
      { label: "7D", days: 7 },
      { label: "30D", days: 30 },
      { label: "60D", days: 60 },
      { label: "180D", days: 180 },
    ],
    []
  );

  async function loadFilters() {
    const j = await fetchJsonWithRetry<FiltersResp>(`${API_BASE_URL}/ops/expenses/filters`);
    if (!j?.ok) throw new Error("Failed to load filters");
    setFilters(j);
  }

  async function loadSalesFilters() {
    const j = await fetchJsonWithRetry<SalesFiltersResp>(`${API_BASE_URL}/ops/sales/filters`);
    if (!j?.ok) throw new Error("Failed to load sales filters");
    setSalesFilters(j);
  }

  async function fetchExpenses(s: string, e: string) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set("start", s);
      params.set("end", e);
      if (ledger) params.set("ledger", ledger);
      if (mainCategory) params.set("main_category", mainCategory);
      if (employee) params.set("employee", employee);
      if (paidFrom) params.set("paid_from", paidFrom);
      if (search.trim()) params.set("q", search.trim());
      if (minAmount.trim()) params.set("min_amount", minAmount.trim());
      if (maxAmount.trim()) params.set("max_amount", maxAmount.trim());
      params.set("limit", String(limit));

      const j = await fetchJsonWithRetry<ExpensesResp>(`${API_BASE_URL}/ops/expenses?${params.toString()}`);
      if (!j?.ok) throw new Error("Failed to load expenses");
      setData(j);
    } catch (e: unknown) {
      setError(friendlyErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  async function fetchSales(s: string, e: string) {
    setSalesLoading(true);
    setSalesError(null);
    try {
      const p1 = new URLSearchParams();
      p1.set("start", s);
      p1.set("end", e);

      const channels = await fetchJsonWithRetry<SalesChannelsResp>(`${API_BASE_URL}/ops/sales/channels?${p1.toString()}`);
      if (!channels?.ok) throw new Error("Failed to load sales channels");
      setSalesChannels(channels);

      const p2 = new URLSearchParams();
      p2.set("start", s);
      p2.set("end", e);
      if (salesOrderType) p2.set("order_type", salesOrderType);
      if (salesDeliveryPartner) p2.set("delivery_partner", salesDeliveryPartner);
      p2.set("limit", "50");

      const items = await fetchJsonWithRetry<TopItemsResp>(`${API_BASE_URL}/ops/sales/top-items?${p2.toString()}`);
      if (!items?.ok) throw new Error("Failed to load top items");
      setTopItems(items);
    } catch (e: unknown) {
      setSalesError(friendlyErrorMessage(e));
    } finally {
      setSalesLoading(false);
    }
  }

  async function loadOpsBrief() {
    setBriefLoading(true);
    setBriefError(null);
    try {
      const j = await fetchJsonWithRetry<unknown>(`${API_BASE_URL}/ops/brief/today`);
      const parsed = parseOpsBrief(j);
      if (!parsed) throw new Error("Failed to parse ops brief");
      setBrief(parsed);
    } catch (e: unknown) {
      setBriefError(friendlyErrorMessage(e));
    } finally {
      setBriefLoading(false);
    }
  }

  async function loadRecentBriefs(days = 7) {
    setRecentLoading(true);
    setRecentError(null);
    try {
      const j = await fetchJsonWithRetry<unknown>(`${API_BASE_URL}/ops/brief/recent?days=${days}`);
      const parsed = parseRecentBriefs(j);
      setRecentBriefs(parsed);
    } catch (e: unknown) {
      setRecentError(friendlyErrorMessage(e));
    } finally {
      setRecentLoading(false);
    }
  }

  useEffect(() => {
    void (async () => {
      try {
        await Promise.all([
          loadFilters(),
          loadSalesFilters(),
          loadOpsBrief(),
          loadRecentBriefs(7),
          fetchExpenses(start, end),
          fetchSales(salesStart, salesEnd),
        ]);
      } catch (e: unknown) {
        setError(friendlyErrorMessage(e) || "Failed to initialize");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function applyPreset(days: number) {
    const e = new Date();
    const s = new Date();
    s.setDate(e.getDate() - days);
    const sIso = toISO(s);
    const eIso = toISO(e);
    setStart(sIso);
    setEnd(eIso);
    void fetchExpenses(sIso, eIso);
  }

  function applyCustom() {
    void fetchExpenses(start, end);
  }

  function applySalesPreset(days: number) {
    const e = new Date();
    const s = new Date();
    s.setDate(e.getDate() - days);
    const sIso = toISO(s);
    const eIso = toISO(e);
    setSalesStart(sIso);
    setSalesEnd(eIso);
    void fetchSales(sIso, eIso);
  }

  function applySalesCustom() {
    void fetchSales(salesStart, salesEnd);
  }

  function syncSalesToExpenses() {
    setSalesStart(start);
    setSalesEnd(end);
    void fetchSales(start, end);
  }

  function exportCsv() {
    const ctx = {
      start: data?.start ?? start,
      end: data?.end ?? end,
      ledger: ledger || "",
      main_category: mainCategory || "",
      employee: employee || "",
      paid_from: paidFrom || "",
      q: search.trim() || "",
      min_amount: minAmount.trim() || "",
      max_amount: maxAmount.trim() || "",
    };
    const rows = (data?.items ?? []).map((r) => ({
      ...ctx,
      expense_date: r.expense_date,
      item_name: r.item_name,
      amount: r.amount,
      ledger_name: r.ledger_name,
      main_category: r.main_category,
      category: r.category,
      paid_from: r.paid_from,
      employee_name: r.employee_name,
    }));
    const f1 = ledger ? `ledger-${safeSlug(ledger)}` : "";
    const f2 = mainCategory ? `main-${safeSlug(mainCategory)}` : "";
    const f3 = employee ? `emp-${safeSlug(employee)}` : "";
    const f4 = paidFrom ? `paid-${safeSlug(paidFrom)}` : "";
    const f5 = search.trim() ? `q-${safeSlug(search.trim())}` : "";
    const suffix = [f1, f2, f3, f4, f5].filter(Boolean).join("__");
    const base = `ops_expenses_${data?.start ?? start}_${data?.end ?? end}`;
    const name = suffix ? `${base}__${suffix}.csv` : `${base}.csv`;
    downloadCsv(name, rows);
  }

  function exportTopItemsCsv() {
    const ctx = {
      start: topItems?.start ?? salesStart,
      end: topItems?.end ?? salesEnd,
      order_type: salesOrderType || "",
      delivery_partner: salesDeliveryPartner || "",
    };
    const rows = (topItems?.items ?? []).map((r) => ({
      ...ctx,
      item_name: r.item_name,
      qty: r.qty,
      revenue: r.revenue,
      order_type_applied: topItems?.filters?.order_type ?? "",
      delivery_partner_applied: topItems?.filters?.delivery_partner ?? "",
    }));
    const f1 = salesOrderType ? `ot-${safeSlug(salesOrderType)}` : "";
    const f2 = salesDeliveryPartner ? `dp-${safeSlug(salesDeliveryPartner)}` : "";
    const suffix = [f1, f2].filter(Boolean).join("__");
    const base = `ops_top_items_${topItems?.start ?? salesStart}_${topItems?.end ?? salesEnd}`;
    const name = suffix ? `${base}__${suffix}.csv` : `${base}.csv`;
    downloadCsv(name, rows);
  }

  const salesPills = useMemo(() => {
    const pills: Array<{ key: string; label: string; onClear?: () => void }> = [];
    pills.push({ key: "sales-dates", label: `Dates: ${salesStart} → ${salesEnd}` });
    if (salesOrderType) pills.push({ key: "sales-ot", label: `Order type: ${salesOrderType}`, onClear: () => setSalesOrderType("") });
    if (salesDeliveryPartner)
      pills.push({
        key: "sales-dp",
        label: `Partner: ${salesDeliveryPartner}`,
        onClear: () => setSalesDeliveryPartner(""),
      });
    return pills;
  }, [salesDeliveryPartner, salesEnd, salesOrderType, salesStart]);

  const briefKpis = brief?.kpis ?? {};
  const briefTopItems = (brief?.top_items_7d ?? []).slice(0, 5);
  const briefDelta = brief?.comparisons?.last_week_same_day?.delta_pct;

  const briefDateValue = toDateValue(brief?.brief_date);
  const latestSalesValue = toDateValue(brief?.data_freshness?.latest_sales_date);
  const latestExpensesValue = toDateValue(brief?.data_freshness?.latest_expenses_date);
  const isStaleSales = briefDateValue !== null && latestSalesValue !== null && latestSalesValue < briefDateValue;
  const isStaleExpenses = briefDateValue !== null && latestExpensesValue !== null && latestExpensesValue < briefDateValue;
  const isStale = isStaleSales || isStaleExpenses;

  const fmtPct = (v: number | null | undefined) => {
    if (v === null || v === undefined) return "—";
    const sign = v > 0 ? "+" : "";
    return `${sign}${Math.round(v * 10) / 10}%`;
  };

  const severityBadge = (sevRaw: string) => {
    const sev = sevRaw.trim().toLowerCase();
    if (sev === "high") return "bg-red-400/20 text-red-100 border-red-800/60";
    if (sev === "medium") return "bg-amber-400/15 text-amber-200 border-amber-900/40";
    if (sev === "low") return "bg-emerald-400/10 text-emerald-200 border-emerald-900/40";
    return "bg-zinc-900 text-zinc-200 border-zinc-800";
  };

  const isSystemOrHigh = (a: OpsBriefAlert) => {
    const tt = (a.task_type ?? "").trim().toLowerCase();
    const sev = (a.severity ?? "").trim().toLowerCase();
    return tt === "system" || sev === "high";
  };

  const alertKey = (a: OpsBriefAlert) => {
    const label = a.title || a.message || "";
    return label.trim().toLowerCase();
  };
  const briefAlerts = useMemo(() => {
    const raw = (brief?.alerts ?? []).filter((a) => Boolean(alertKey(a)));
    const prioritized = raw.slice().sort((a, b) => {
      const ap = isSystemOrHigh(a) ? 1 : 0;
      const bp = isSystemOrHigh(b) ? 1 : 0;
      return bp - ap;
    });

    const seen = new Set<string>();
    const deduped: OpsBriefAlert[] = [];
    for (const a of prioritized) {
      const key = alertKey(a);
      if (!key) continue;
      if (seen.has(key)) continue;
      seen.add(key);
      deduped.push(a);
      if (deduped.length >= 5) break;
    }
    return deduped;
  }, [brief?.alerts]);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab("expenses")}
            className={
              activeTab === "expenses"
                ? "rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950"
                : "rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-900"
            }
          >
            Expenses
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("sales")}
            className={
              activeTab === "sales"
                ? "rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950"
                : "rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-xs font-semibold text-zinc-200 hover:bg-zinc-900"
            }
          >
            Sales
          </button>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-zinc-100">Anomalies</div>
              <div className="mt-1 text-xs text-zinc-500">Quick alerts to catch unusual spikes and drops.</div>
            </div>
            <div className="rounded-full border border-zinc-800 bg-zinc-950 px-3 py-1 text-[11px] text-zinc-400">Coming soon</div>
          </div>
          <div className="mt-3 grid gap-2">
            <div className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-xs text-zinc-200">Ingredient cost spike: Oil</div>
              <div className="rounded-full bg-amber-400/10 px-2 py-0.5 text-[11px] font-semibold text-amber-300">Watch</div>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-xs text-zinc-200">Delivery partner drop: Swiggy</div>
              <div className="rounded-full bg-red-400/10 px-2 py-0.5 text-[11px] font-semibold text-red-300">High</div>
            </div>
            <div className="flex items-center justify-between rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-xs text-zinc-200">Cash expense outlier</div>
              <div className="rounded-full bg-zinc-800/60 px-2 py-0.5 text-[11px] font-semibold text-zinc-300">Info</div>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-zinc-100">Ops Brief (Yesterday)</div>
              <div className="mt-1 text-xs text-zinc-500">Auto-generated snapshot with KPIs, insights, and alerts.</div>
              {(brief?.data_freshness?.latest_sales_date || brief?.data_freshness?.latest_expenses_date) ? (
                <div className="mt-2 text-[11px] text-zinc-500">
                  Data freshness:
                  <span className="ml-2 text-zinc-300">Sales {brief?.data_freshness?.latest_sales_date ?? "—"}</span>
                  <span className="ml-2 text-zinc-300">Expenses {brief?.data_freshness?.latest_expenses_date ?? "—"}</span>
                </div>
              ) : null}
            </div>
            <div className="flex items-center gap-2">
              {brief?.brief_date ? (
                <div className="rounded-full border border-zinc-800 bg-zinc-950 px-3 py-1 text-[11px] text-zinc-400">{brief.brief_date}</div>
              ) : null}
              <button
                type="button"
                onClick={() => loadOpsBrief()}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
                disabled={briefLoading}
              >
                Refresh
              </button>
            </div>
          </div>
          {briefError ? (
            <div className="mt-3 rounded-xl border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs text-red-200">{briefError}</div>
          ) : null}

          {!briefLoading && !briefError && isStale ? (
            <div className="mt-3 rounded-xl border border-amber-900/40 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
              <div className="font-semibold">Data looks stale for this brief.</div>
              <div className="mt-0.5 text-[11px] text-amber-200/80">Run sync + regenerate brief.</div>
            </div>
          ) : null}

          <div className="mt-3 grid gap-2 md:grid-cols-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-[11px] text-zinc-500">Revenue</div>
              {briefLoading ? <div className="mt-2 h-4 w-24 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtINR(briefKpis.revenue ?? 0)}</div>}
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-[11px] text-zinc-500">Expenses</div>
              {briefLoading ? <div className="mt-2 h-4 w-24 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtINR(briefKpis.expenses ?? 0)}</div>}
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-[11px] text-zinc-500">Net</div>
              {briefLoading ? <div className="mt-2 h-4 w-24 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtINR(briefKpis.net ?? ((briefKpis.revenue ?? 0) - (briefKpis.expenses ?? 0)))}</div>}
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
              <div className="text-[11px] text-zinc-500">Orders</div>
              {briefLoading ? <div className="mt-2 h-4 w-16 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{Math.round(briefKpis.orders ?? 0)}</div>}
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-3">
            <div className="text-xs font-semibold text-zinc-100">Compared to last week (same day)</div>
            <div className="mt-2 grid gap-2 md:grid-cols-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
                <div className="text-[11px] text-zinc-500">Revenue</div>
                {briefLoading ? <div className="mt-2 h-3 w-16 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtPct(briefDelta?.revenue)}</div>}
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
                <div className="text-[11px] text-zinc-500">Expenses</div>
                {briefLoading ? <div className="mt-2 h-3 w-16 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtPct(briefDelta?.expenses)}</div>}
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
                <div className="text-[11px] text-zinc-500">Net</div>
                {briefLoading ? <div className="mt-2 h-3 w-16 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtPct(briefDelta?.net)}</div>}
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">
                <div className="text-[11px] text-zinc-500">Orders</div>
                {briefLoading ? <div className="mt-2 h-3 w-16 animate-pulse rounded bg-zinc-800" /> : <div className="mt-1 text-sm font-semibold text-zinc-100">{fmtPct(briefDelta?.orders)}</div>}
              </div>
            </div>
          </div>

          <div className="mt-3 grid gap-3 md:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-3">
              <div className="text-xs font-semibold text-zinc-100">Insights</div>
              <div className="mt-2 grid gap-2">
                {briefLoading ? (
                  <>
                    <div className="h-3 w-full animate-pulse rounded bg-zinc-800" />
                    <div className="h-3 w-5/6 animate-pulse rounded bg-zinc-800" />
                    <div className="h-3 w-4/6 animate-pulse rounded bg-zinc-800" />
                  </>
                ) : (brief?.insights?.length ?? 0) ? (
                  (brief?.insights ?? []).slice(0, 5).map((x, i) => (
                    <div key={`ins-${i}`} className="text-xs text-zinc-200">
                      {x}
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-zinc-500">No insights available.</div>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-3">
              <div className="text-xs font-semibold text-zinc-100">Alerts</div>
              <div className="mt-2 grid gap-2">
                {briefLoading ? (
                  <>
                    <div className="h-3 w-5/6 animate-pulse rounded bg-zinc-800" />
                    <div className="h-3 w-4/6 animate-pulse rounded bg-zinc-800" />
                    <div className="h-3 w-3/6 animate-pulse rounded bg-zinc-800" />
                  </>
                ) : briefAlerts.length ? (
                  briefAlerts.map((a, i) => (
                    <div key={`al-${i}`} className="flex items-start justify-between gap-3 rounded-lg border border-zinc-800 bg-zinc-950 px-2 py-2">
                      <div>
                        <div className="text-xs font-semibold text-zinc-100">{a.title || a.message || "—"}</div>
                        {a.title && a.message ? <div className="mt-0.5 text-[11px] text-zinc-500">{a.message}</div> : null}
                      </div>
                      <div className="flex shrink-0 items-center gap-2">
                        {a.task_type ? (
                          <div className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${isSystemOrHigh(a) ? "bg-violet-400/15 text-violet-200 border-violet-900/50" : "bg-zinc-900 text-zinc-200 border-zinc-800"}`}>
                            {a.task_type}
                          </div>
                        ) : null}
                        {a.severity ? (
                          <div className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${severityBadge(a.severity)}`}>{a.severity}</div>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-zinc-500">No alerts.</div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-3">
            <div className="text-xs font-semibold text-zinc-100">Top items (last 7 days)</div>
            <div className="mt-2 overflow-auto">
              <table className="min-w-[520px] w-full text-left text-xs">
                <thead className="sticky top-0 bg-zinc-950">
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="px-3 py-2">Item</th>
                    <th className="px-3 py-2">Qty</th>
                    <th className="px-3 py-2">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {briefLoading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={`brief-ti-${i}`} className="border-b border-zinc-900/60">
                        <td className="px-3 py-2">
                          <div className="h-3 w-56 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-16 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                      </tr>
                    ))
                  ) : briefTopItems.length ? (
                    briefTopItems.map((r, i) => (
                      <tr key={`brief-ti-row-${i}`} className="border-b border-zinc-900/60 text-zinc-200">
                        <td className="px-3 py-2 min-w-[280px]">
                          <div className="font-medium text-zinc-100">{r.item_name || "—"}</div>
                        </td>
                        <td className="px-3 py-2 whitespace-nowrap text-zinc-300">{Math.round((r.qty ?? 0) * 100) / 100}</td>
                        <td className="px-3 py-2 whitespace-nowrap font-semibold">{fmtINR(r.revenue ?? 0)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-3 py-4 text-xs text-zinc-500" colSpan={3}>
                        No top items available.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-3 rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-3">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-zinc-100">Recent briefs (last 7 days)</div>
              <button
                type="button"
                onClick={() => loadRecentBriefs(7)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
                disabled={recentLoading}
              >
                Refresh
              </button>
            </div>

            {recentError ? (
              <div className="mt-3 rounded-xl border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs text-red-200">{recentError}</div>
            ) : null}

            <div className="mt-2 overflow-auto">
              <table className="min-w-[640px] w-full text-left text-xs">
                <thead className="sticky top-0 bg-zinc-950">
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="px-3 py-2">Date</th>
                    <th className="px-3 py-2">Revenue</th>
                    <th className="px-3 py-2">Expenses</th>
                    <th className="px-3 py-2">Net</th>
                    <th className="px-3 py-2">Orders</th>
                  </tr>
                </thead>
                <tbody>
                  {recentLoading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                      <tr key={`rb-skel-${i}`} className="border-b border-zinc-900/60">
                        <td className="px-3 py-2">
                          <div className="h-3 w-20 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-3 py-2">
                          <div className="h-3 w-16 animate-pulse rounded bg-zinc-800" />
                        </td>
                      </tr>
                    ))
                  ) : recentBriefs.length ? (
                    recentBriefs.slice(0, 7).map((b, i) => (
                      <tr key={`rb-${i}`} className="border-b border-zinc-900/60 text-zinc-200">
                        <td className="px-3 py-2 whitespace-nowrap text-zinc-300">{b.brief_date || "—"}</td>
                        <td className="px-3 py-2 whitespace-nowrap font-semibold">{fmtINR(b.kpis?.revenue ?? 0)}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{fmtINR(b.kpis?.expenses ?? 0)}</td>
                        <td className="px-3 py-2 whitespace-nowrap">{fmtINR(b.kpis?.net ?? ((b.kpis?.revenue ?? 0) - (b.kpis?.expenses ?? 0)))}</td>
                        <td className="px-3 py-2 whitespace-nowrap text-zinc-300">{Math.round(b.kpis?.orders ?? 0)}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="px-3 py-4 text-xs text-zinc-500" colSpan={5}>
                        No recent briefs.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {activeTab === "expenses" ? (
        <>
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-zinc-100">Expense Explorer</div>
            <div className="mt-1 text-xs text-zinc-500">
              Filter expenses by date range, ledger/category, amount, and keyword.
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
                disabled={loading}
              />
              <span className="text-xs text-zinc-500">to</span>
              <input
                type="date"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={loading}
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

        <div className="mt-4 grid gap-3 lg:grid-cols-6">
          <div className="lg:col-span-2">
            <div className="text-xs text-zinc-500">Ledger</div>
            <select
              value={ledger}
              onChange={(e) => setLedger(e.target.value)}
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
              disabled={loading}
            >
              <option value="">All</option>
              {(filters?.ledgers ?? []).map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
          </div>

          <div className="lg:col-span-2">
            <div className="text-xs text-zinc-500">Main category</div>
            <select
              value={mainCategory}
              onChange={(e) => setMainCategory(e.target.value)}
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
              disabled={loading}
            >
              <option value="">All</option>
              {(filters?.main_categories ?? []).map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
          </div>

          <div className="lg:col-span-2">
            <div className="text-xs text-zinc-500">Search</div>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="e.g. rent / electricity / diesel"
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600"
              disabled={loading}
            />
          </div>

          {filters?.has_paid_from ? (
            <div className="lg:col-span-2">
              <div className="text-xs text-zinc-500">Paid from</div>
              <select
                value={paidFrom}
                onChange={(e) => setPaidFrom(e.target.value)}
                className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={loading}
              >
                <option value="">All</option>
                {(filters?.paid_froms ?? []).map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          {filters?.has_employee ? (
            <div className="lg:col-span-2">
              <div className="text-xs text-zinc-500">Employee</div>
              <select
                value={employee}
                onChange={(e) => setEmployee(e.target.value)}
                className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={loading}
              >
                <option value="">All</option>
                {(filters?.employees ?? []).map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          <div>
            <div className="text-xs text-zinc-500">Min ₹</div>
            <input
              value={minAmount}
              onChange={(e) => setMinAmount(e.target.value)}
              placeholder="0"
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600"
              disabled={loading}
            />
          </div>

          <div>
            <div className="text-xs text-zinc-500">Max ₹</div>
            <input
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              placeholder="100000"
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 placeholder:text-zinc-600"
              disabled={loading}
            />
          </div>

          <div>
            <div className="text-xs text-zinc-500">Limit</div>
            <select
              value={String(limit)}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="mt-1 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
              disabled={loading}
            >
              {[100, 200, 500, 1000, 2000].map((n) => (
                <option key={n} value={String(n)}>
                  {n}
                </option>
              ))}
            </select>
          </div>

          <div className="lg:col-span-6 flex flex-wrap items-center justify-between gap-2 pt-2">
            <div className="text-xs text-zinc-500">
              Rows: <span className="text-zinc-200">{data?.summary?.row_count ?? 0}</span> • Total: <span className="text-zinc-200">{fmtINR(data?.summary?.total_amount ?? 0)}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => fetchExpenses(start, end)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
                disabled={loading}
              >
                Refresh
              </button>
              <button
                type="button"
                onClick={() => exportCsv()}
                className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950 hover:bg-emerald-300 disabled:opacity-60"
                disabled={loading || !(data?.items?.length ?? 0)}
              >
                Export CSV
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950">
        <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
          <div>
            <div className="text-sm font-semibold text-zinc-100">Expenses</div>
            <div className="text-xs text-zinc-500">Sorted by expense_date desc</div>
          </div>
          {loading ? <div className="text-xs text-zinc-500">Loading…</div> : null}
        </div>

        <div className="overflow-auto">
          <table className="min-w-[860px] w-full text-left text-xs">
            <thead className="sticky top-0 bg-zinc-950">
              <tr className="border-b border-zinc-800 text-zinc-400">
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Ledger</th>
                <th className="px-4 py-3">Main</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Paid from</th>
                <th className="px-4 py-3">Employee</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={`exp-skel-${i}`} className="border-b border-zinc-900/60">
                    <td className="px-4 py-3">
                      <div className="h-3 w-20 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-64 animate-pulse rounded bg-zinc-800" />
                      <div className="mt-2 h-3 w-28 animate-pulse rounded bg-zinc-900" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-28 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-20 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                    </td>
                  </tr>
                ))
              ) : null}
              {(data?.items ?? []).map((r, i) => (
                <tr key={i} className="border-b border-zinc-900/60 text-zinc-200">
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-300">{r.expense_date}</td>
                  <td className="px-4 py-3 min-w-[280px]">
                    <div className="font-medium text-zinc-100">{r.item_name || "—"}</div>
                    <div className="mt-0.5 text-[11px] text-zinc-500">{r.category || ""}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">{r.ledger_name || "—"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-300">{r.main_category || "—"}</td>
                  <td className="px-4 py-3 whitespace-nowrap font-semibold">{fmtINR(r.amount || 0)}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-300">{r.paid_from || "—"}</td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-300">{r.employee_name || "—"}</td>
                </tr>
              ))}
              {!loading && !(data?.items?.length ?? 0) ? (
                <tr>
                  <td className="px-4 py-8 text-sm text-zinc-500" colSpan={7}>
                    <div className="text-zinc-200">No results found.</div>
                    <div className="mt-1 text-xs text-zinc-500">Try widening the date range or clearing a filter.</div>
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

        </>
      ) : null}

      {activeTab === "sales" ? (
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 px-4 py-3">
          <div>
            <div className="text-sm font-semibold text-zinc-100">Sales drilldowns</div>
            <div className="text-xs text-zinc-500">Channels and top items for the selected date range</div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap items-center gap-2">
              {presets.map((p) => (
                <button
                  key={`sales-${p.label}`}
                  type="button"
                  onClick={() => applySalesPreset(p.days)}
                  className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900"
                  disabled={salesLoading}
                >
                  {p.label}
                </button>
              ))}
              <div className="mx-2 hidden h-6 w-px bg-zinc-800 md:block" />
              <input
                type="date"
                value={salesStart}
                onChange={(e) => setSalesStart(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={salesLoading}
              />
              <span className="text-xs text-zinc-500">to</span>
              <input
                type="date"
                value={salesEnd}
                onChange={(e) => setSalesEnd(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={salesLoading}
              />
              <button
                type="button"
                onClick={() => applySalesCustom()}
                className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950 hover:bg-emerald-300 disabled:opacity-60"
                disabled={salesLoading}
              >
                Apply
              </button>
              <button
                type="button"
                onClick={() => syncSalesToExpenses()}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
                disabled={salesLoading}
              >
                Same period as expenses
              </button>
            </div>

            {salesFilters?.has_order_type ? (
              <select
                value={salesOrderType}
                onChange={(e) => setSalesOrderType(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={salesLoading}
              >
                <option value="">All order types</option>
                {(salesFilters?.order_types ?? []).map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            ) : null}

            {salesFilters?.has_delivery_partner ? (
              <select
                value={salesDeliveryPartner}
                onChange={(e) => setSalesDeliveryPartner(e.target.value)}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200"
                disabled={salesLoading}
              >
                <option value="">All delivery partners</option>
                {(salesFilters?.delivery_partners ?? []).map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            ) : null}

            <button
              type="button"
              onClick={() => fetchSales(salesStart, salesEnd)}
              className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
              disabled={salesLoading}
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => exportTopItemsCsv()}
              className="rounded-xl bg-emerald-400 px-4 py-2 text-xs font-semibold text-zinc-950 hover:bg-emerald-300 disabled:opacity-60"
              disabled={salesLoading || !(topItems?.items?.length ?? 0)}
            >
              Export CSV
            </button>
          </div>
        </div>

        {salesPills.length ? (
          <div className="flex flex-wrap items-center gap-2 border-b border-zinc-800 px-4 py-3">
            {salesPills.map((p) => (
              <div
                key={p.key}
                className="flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-200"
              >
                <span className="text-zinc-300">{p.label}</span>
                {p.onClear ? (
                  <button
                    type="button"
                    onClick={p.onClear}
                    className="rounded-full border border-zinc-800 bg-zinc-950 px-2 py-0.5 text-[11px] text-zinc-200 hover:bg-zinc-900"
                    disabled={salesLoading}
                  >
                    Clear
                  </button>
                ) : null}
              </div>
            ))}
            {(salesOrderType || salesDeliveryPartner) ? (
              <button
                type="button"
                onClick={() => {
                  setSalesOrderType("");
                  setSalesDeliveryPartner("");
                }}
                className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs text-zinc-200 hover:bg-zinc-900 disabled:opacity-60"
                disabled={salesLoading}
              >
                Clear filters
              </button>
            ) : null}
          </div>
        ) : null}

        {salesError ? (
          <div className="px-4 pt-3">
            <div className="rounded-xl border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs text-red-200">
              {salesError}
            </div>
          </div>
        ) : null}

        <div className="grid gap-4 p-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-950">
            <div className="border-b border-zinc-800 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-100">Revenue by order type</div>
            </div>
            <div className="overflow-auto">
              <table className="min-w-[520px] w-full text-left text-xs">
                <thead className="sticky top-0 bg-zinc-950">
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="px-4 py-3">Order type</th>
                    <th className="px-4 py-3">Revenue</th>
                    <th className="px-4 py-3">Orders</th>
                  </tr>
                </thead>
                <tbody>
                  {salesLoading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                      <tr key={`ot-skel-${i}`} className="border-b border-zinc-900/60">
                        <td className="px-4 py-3">
                          <div className="h-3 w-28 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-4 py-3">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-4 py-3">
                          <div className="h-3 w-16 animate-pulse rounded bg-zinc-800" />
                        </td>
                      </tr>
                    ))
                  ) : null}
                  {(salesChannels?.order_types ?? []).map((r, i) => (
                    <tr key={i} className="border-b border-zinc-900/60 text-zinc-200">
                      <td className="px-4 py-3">{r.channel || "—"}</td>
                      <td className="px-4 py-3 font-semibold">{fmtINR(r.revenue || 0)}</td>
                      <td className="px-4 py-3 text-zinc-300">{r.orders ?? 0}</td>
                    </tr>
                  ))}
                  {!salesLoading && !(salesChannels?.order_types?.length ?? 0) ? (
                    <tr>
                      <td className="px-4 py-6 text-sm text-zinc-500" colSpan={3}>
                        No data.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-950">
            <div className="border-b border-zinc-800 px-4 py-3">
              <div className="text-sm font-semibold text-zinc-100">Revenue by delivery partner</div>
            </div>
            <div className="overflow-auto">
              <table className="min-w-[520px] w-full text-left text-xs">
                <thead className="sticky top-0 bg-zinc-950">
                  <tr className="border-b border-zinc-800 text-zinc-400">
                    <th className="px-4 py-3">Partner</th>
                    <th className="px-4 py-3">Revenue</th>
                    <th className="px-4 py-3">Orders</th>
                  </tr>
                </thead>
                <tbody>
                  {salesLoading ? (
                    Array.from({ length: 6 }).map((_, i) => (
                      <tr key={`dp-skel-${i}`} className="border-b border-zinc-900/60">
                        <td className="px-4 py-3">
                          <div className="h-3 w-28 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-4 py-3">
                          <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                        </td>
                        <td className="px-4 py-3">
                          <div className="h-3 w-16 animate-pulse rounded bg-zinc-800" />
                        </td>
                      </tr>
                    ))
                  ) : null}
                  {(salesChannels?.delivery_partners ?? []).map((r, i) => (
                    <tr key={i} className="border-b border-zinc-900/60 text-zinc-200">
                      <td className="px-4 py-3">{r.channel || "—"}</td>
                      <td className="px-4 py-3 font-semibold">{fmtINR(r.revenue || 0)}</td>
                      <td className="px-4 py-3 text-zinc-300">{r.orders ?? 0}</td>
                    </tr>
                  ))}
                  {!salesLoading && !(salesChannels?.delivery_partners?.length ?? 0) ? (
                    <tr>
                      <td className="px-4 py-6 text-sm text-zinc-500" colSpan={3}>
                        No data.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="border-t border-zinc-800 px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-zinc-100">Top items</div>
              <div className="text-xs text-zinc-500">By revenue (line-item aggregated)</div>
            </div>
            {salesLoading ? <div className="text-xs text-zinc-500">Loading…</div> : null}
          </div>
        </div>
        <div className="overflow-auto">
          <table className="min-w-[520px] w-full text-left text-xs">
            <thead className="sticky top-0 bg-zinc-950">
              <tr className="border-b border-zinc-800 text-zinc-400">
                <th className="px-4 py-3">Item</th>
                <th className="px-4 py-3">Qty</th>
                <th className="px-4 py-3">Revenue</th>
              </tr>
            </thead>
            <tbody>
              {salesLoading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={`ti-skel-${i}`} className="border-b border-zinc-900/60">
                    <td className="px-4 py-3">
                      <div className="h-3 w-56 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-16 animate-pulse rounded bg-zinc-800" />
                    </td>
                    <td className="px-4 py-3">
                      <div className="h-3 w-24 animate-pulse rounded bg-zinc-800" />
                    </td>
                  </tr>
                ))
              ) : null}
              {(topItems?.items ?? []).map((r, i) => (
                <tr key={i} className="border-b border-zinc-900/60 text-zinc-200">
                  <td className="px-4 py-3 min-w-[280px]">
                    <div className="font-medium text-zinc-100">{r.item_name || "—"}</div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-zinc-300">{Math.round((r.qty ?? 0) * 100) / 100}</td>
                  <td className="px-4 py-3 whitespace-nowrap font-semibold">{fmtINR(r.revenue || 0)}</td>
                </tr>
              ))}
              {!salesLoading && !(topItems?.items?.length ?? 0) ? (
                <tr>
                  <td className="px-4 py-6 text-sm text-zinc-500" colSpan={3}>
                    No data.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      ) : null}

      <div className="text-xs text-zinc-500">
        Next in Operations: anomaly views and automated operational alerts.
      </div>
    </div>
  );
}
