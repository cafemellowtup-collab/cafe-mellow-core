"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  FileText, 
  Sparkles, 
  Download, 
  RefreshCw, 
  Calendar,
  TrendingUp,
  DollarSign,
  Package,
  Users,
  BarChart3,
  PieChart,
  Send,
  Clock
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  data_sources: string[];
  refresh_frequency: string;
}

type ReportPeriod = {
  start_date?: string;
  end_date?: string;
  date?: string;
  [key: string]: unknown;
};

interface Report {
  report_type: string;
  generated_at: string;
  period: ReportPeriod;
  summary?: Record<string, unknown>;
  insights?: string[];
  charts?: Record<string, unknown>;
  profit_loss?: Record<string, number | string>;
  ai_analysis?: string;
  expense_breakdown?: Array<{ category: string; count: number; total: number }>;
  [key: string]: unknown;
}

const CHART_COLORS = ["#34d399", "#22d3ee", "#a78bfa", "#f472b6", "#fbbf24"];

const QUICK_REPORTS = [
  { id: "today", label: "Today's Summary", icon: Calendar },
  { id: "yesterday", label: "Yesterday", icon: Clock },
  { id: "this_week", label: "This Week", icon: TrendingUp },
  { id: "this_month", label: "This Month", icon: BarChart3 },
];

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  operations: Package,
  finance: DollarSign,
  analytics: BarChart3,
  hr: Users,
  crm: Users,
};

export default function ReportsPage() {
  const { tenant } = useTenant();
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");
  const [dateRange, setDateRange] = useState({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reports/templates`);
      if (res.ok) {
        const data = await res.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error("Failed to fetch templates:", error);
    }
  };

  const generateQuickReport = async (reportType: string) => {
    setLoading(true);
    setReport(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/reports/quick/${reportType}?tenant_id=${tenant.org_id}`
      );
      if (res.ok) {
        setReport(await res.json());
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateTemplateReport = async (templateId: string) => {
    setLoading(true);
    setReport(null);
    setSelectedTemplate(templateId);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reports/generate?tenant_id=${tenant.org_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: templateId,
          start_date: dateRange.start,
          end_date: dateRange.end,
        }),
      });
      if (res.ok) {
        setReport(await res.json());
      }
    } catch (error) {
      console.error("Failed to generate report:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateCustomReport = async () => {
    if (!customPrompt.trim()) return;
    
    setLoading(true);
    setReport(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reports/generate?tenant_id=${tenant.org_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: "custom",
          custom_prompt: customPrompt,
          start_date: dateRange.start,
          end_date: dateRange.end,
        }),
      });
      if (res.ok) {
        setReport(await res.json());
      }
    } catch (error) {
      console.error("Failed to generate custom report:", error);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async (format: "json" | "markdown" | "csv") => {
    if (!report) return;
    
    try {
      const reportType = report.report_type === "daily_summary" ? "daily" : 
                        report.report_type === "weekly_pnl" ? "weekly" : "monthly";
      
      const res = await fetch(
        `${API_BASE_URL}/api/v1/reports/export/${reportType}?format=${format}&tenant_id=${tenant.org_id}`
      );
      
      if (res.ok) {
        const data = await res.json();
        
        // Create download
        const blob = new Blob(
          [format === "json" ? JSON.stringify(data, null, 2) : data.content],
          { type: format === "json" ? "application/json" : "text/plain" }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `report_${report.report_type}_${new Date().toISOString().split("T")[0]}.${format === "markdown" ? "md" : format}`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  const formatCurrency = (value: number) => `₹${value.toLocaleString("en-IN")}`;

  type ChartType = "line" | "bar" | "area" | "pie";
  type ChartConfig = {
    type: ChartType;
    data: Array<Record<string, unknown>>;
    xKey: string;
    yKey: string;
    title: string;
  };

  const renderChart = (chartConfig: unknown) => {
    if (!chartConfig || typeof chartConfig !== "object") return null;
    const cfg = chartConfig as Partial<ChartConfig>;
    if (!cfg.type || !cfg.data || !Array.isArray(cfg.data) || cfg.data.length === 0) return null;

    const type = cfg.type;
    const data = cfg.data;
    const xKey = cfg.xKey ?? "name";
    const yKey = cfg.yKey ?? "value";
    const title = cfg.title ?? "Chart";

    return (
      <div className="rounded-xl border border-white/10 bg-black/30 p-4">
        <div className="mb-3 text-sm font-semibold text-emerald-200">{title}</div>
        <ResponsiveContainer width="100%" height={200}>
          {type === "line" ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "rgba(0,0,0,0.9)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px" }} />
              <Line type="monotone" dataKey={yKey} stroke="#34d399" strokeWidth={2} dot={{ fill: "#34d399" }} />
            </LineChart>
          ) : type === "bar" ? (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "rgba(0,0,0,0.9)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px" }} />
              <Bar dataKey={yKey} fill="#34d399" radius={[4, 4, 0, 0]} />
            </BarChart>
          ) : type === "area" ? (
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey={xKey} stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "rgba(0,0,0,0.9)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px" }} />
              <Area type="monotone" dataKey={yKey} stroke="#34d399" fill="rgba(52,211,153,0.2)" />
            </AreaChart>
          ) : type === "pie" ? (
            <RechartsPie>
              <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={70} label={({ name }) => name}>
                {data.map((_, index: number) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: "rgba(0,0,0,0.9)", border: "1px solid rgba(52,211,153,0.3)", borderRadius: "8px" }} />
            </RechartsPie>
          ) : null}
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Reports</h1>
          <p className="text-sm text-zinc-400">Generate AI-powered reports and analytics</p>
        </div>
      </div>

      {/* Quick Reports */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {QUICK_REPORTS.map((qr) => (
          <motion.button
            key={qr.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => generateQuickReport(qr.id)}
            disabled={loading}
            className="flex items-center gap-3 rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 p-4 text-left transition hover:border-emerald-500/30 disabled:opacity-50"
          >
            <div className="rounded-lg bg-emerald-500/20 p-2">
              <qr.icon size={20} className="text-emerald-400" />
            </div>
            <div>
              <div className="font-semibold text-white">{qr.label}</div>
              <div className="text-xs text-zinc-500">Quick report</div>
            </div>
          </motion.button>
        ))}
      </div>

      {/* AI Custom Report */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-purple-500/5 p-5"
      >
        <div className="mb-4 flex items-center gap-2">
          <Sparkles size={20} className="text-violet-400" />
          <h3 className="text-lg font-semibold text-white">AI-Generated Custom Report</h3>
        </div>
        
        <div className="mb-4 flex flex-wrap gap-3">
          <div>
            <label className="mb-1 block text-xs text-zinc-400">Start Date</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-violet-500/50"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-zinc-400">End Date</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-violet-500/50"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <input
            type="text"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            placeholder="Describe the report you need... e.g., 'Compare this week's sales to last week and identify top performing items'"
            className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50"
            onKeyDown={(e) => e.key === "Enter" && generateCustomReport()}
          />
          <button
            onClick={generateCustomReport}
            disabled={loading || !customPrompt.trim()}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition hover:shadow-violet-500/40 disabled:opacity-50"
          >
            <Send size={16} />
            Generate
          </button>
        </div>
      </motion.div>

      {/* Report Templates */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-white">Pre-styled Report Templates</h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => {
            const Icon = CATEGORY_ICONS[template.category] || FileText;
            return (
              <motion.button
                key={template.id}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => generateTemplateReport(template.id)}
                disabled={loading}
                className={`rounded-xl border p-4 text-left transition ${
                  selectedTemplate === template.id
                    ? "border-emerald-500/50 bg-emerald-500/10"
                    : "border-white/10 bg-white/5 hover:border-white/20"
                } disabled:opacity-50`}
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="rounded-lg bg-emerald-500/20 p-2">
                    <Icon size={18} className="text-emerald-400" />
                  </div>
                  <span className="rounded-full bg-zinc-700/50 px-2 py-0.5 text-[10px] font-medium text-zinc-300">
                    {template.category}
                  </span>
                </div>
                <div className="font-semibold text-white">{template.name}</div>
                <div className="mt-1 text-xs text-zinc-400 line-clamp-2">{template.description}</div>
                <div className="mt-2 text-[10px] text-zinc-500">
                  Refresh: {template.refresh_frequency}
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
          <RefreshCw size={32} className="mx-auto animate-spin text-emerald-400" />
          <p className="mt-4 text-sm text-zinc-400">Generating report...</p>
        </div>
      )}

      {/* Report Display */}
      {report && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-6"
        >
          {/* Report Header */}
          <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-white">
                {report.report_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </h2>
              <p className="text-sm text-zinc-400">
                Generated: {new Date(report.generated_at).toLocaleString()}
              </p>
              {report.period && (
                <p className="text-xs text-zinc-500">
                  Period: {report.period.start_date || report.period.date} 
                  {report.period.end_date && ` to ${report.period.end_date}`}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => exportReport("json")}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-300 transition hover:bg-white/10"
              >
                <Download size={14} />
                JSON
              </button>
              <button
                onClick={() => exportReport("markdown")}
                className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-300 transition hover:bg-white/10"
              >
                <Download size={14} />
                Markdown
              </button>
            </div>
          </div>

          {/* Summary KPIs */}
          {report.summary && (
            <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(report.summary).map(([key, value]) => (
                <div key={key} className="rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 p-4">
                  <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                    {key.replace(/_/g, " ")}
                  </div>
                  <div className="mt-1 text-2xl font-bold text-white">
                    {typeof value === "number" 
                      ? key.includes("revenue") || key.includes("expense") || key.includes("profit") || key.includes("cost")
                        ? formatCurrency(value)
                        : key.includes("margin") || key.includes("percentage")
                          ? `${value}%`
                          : value.toLocaleString()
                      : String(value ?? "")
                    }
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Profit/Loss Section */}
          {report.profit_loss && (
            <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {Object.entries(report.profit_loss).map(([key, value]) => (
                <div key={key} className={`rounded-xl border p-4 ${
                  key === "net_profit" 
                    ? (value as number) >= 0 
                      ? "border-emerald-500/30 bg-emerald-500/10" 
                      : "border-red-500/30 bg-red-500/10"
                    : "border-white/10 bg-white/5"
                }`}>
                  <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">
                    {key.replace(/_/g, " ")}
                  </div>
                  <div className={`mt-1 text-2xl font-bold ${
                    key === "net_profit" 
                      ? (value as number) >= 0 ? "text-emerald-400" : "text-red-400"
                      : "text-white"
                  }`}>
                    {typeof value === "number"
                      ? key.includes("margin") ? `${value}%` : formatCurrency(value)
                      : String(value ?? "")
                    }
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Insights */}
          {report.insights && report.insights.length > 0 && (
            <div className="mb-6">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-emerald-200">Key Insights</h3>
              <div className="space-y-2">
                {report.insights.map((insight, i) => (
                  <div key={i} className="flex items-start gap-2 rounded-lg bg-black/20 px-4 py-3 text-sm text-zinc-300">
                    <span className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                    {insight}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Charts */}
          {report.charts && Object.keys(report.charts).length > 0 && (
            <div className="grid gap-4 lg:grid-cols-2">
              {Object.entries(report.charts).map(([key, chartConfig]) => (
                <div key={key}>{renderChart(chartConfig)}</div>
              ))}
            </div>
          )}

          {/* AI Analysis for custom reports */}
          {report.ai_analysis && (
            <div className="mt-6 rounded-xl border border-violet-500/20 bg-violet-500/10 p-4">
              <h3 className="mb-2 text-sm font-semibold text-violet-200">AI Analysis</h3>
              <div className="whitespace-pre-wrap text-sm text-zinc-300">{report.ai_analysis}</div>
            </div>
          )}

          {/* Expense Breakdown Table */}
          {report.expense_breakdown && report.expense_breakdown.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-emerald-200">Expense Breakdown</h3>
              <div className="overflow-hidden rounded-xl border border-white/10">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10 bg-black/30">
                      <th className="px-4 py-2 text-left text-xs font-semibold uppercase text-zinc-400">Category</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold uppercase text-zinc-400">Count</th>
                      <th className="px-4 py-2 text-right text-xs font-semibold uppercase text-zinc-400">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {report.expense_breakdown.map((item, i: number) => (
                      <tr key={i} className="hover:bg-white/5">
                        <td className="px-4 py-2 text-sm text-white">{item.category}</td>
                        <td className="px-4 py-2 text-right text-sm text-zinc-400">{item.count}</td>
                        <td className="px-4 py-2 text-right text-sm font-medium text-emerald-400">
                          {formatCurrency(item.total)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
