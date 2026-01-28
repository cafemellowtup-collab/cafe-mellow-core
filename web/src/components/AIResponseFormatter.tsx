"use client";

import { useMemo } from "react";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  AlertTriangle,
  CheckCircle,
  Info,
  Target,
  DollarSign,
  Users,
  Package,
  Clock
} from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  AreaChart,
  Area
} from "recharts";

// ==================== Types ====================

interface ParsedData {
  type: "kpi" | "table" | "chart" | "task" | "finding" | "action" | "text";
  content: any;
}

interface KPIData {
  label: string;
  value: string | number;
  change?: number;
  trend?: "up" | "down" | "neutral";
  unit?: string;
}

interface TableData {
  headers: string[];
  rows: (string | number)[][];
}

interface ChartData {
  type: "line" | "bar" | "pie" | "area";
  title: string;
  data: Record<string, any>[];
  xKey: string;
  yKey: string | string[];
}

interface TaskData {
  id: string;
  title: string;
  priority: "high" | "medium" | "low";
  assignee?: string;
  due?: string;
}

interface FindingData {
  type: "issue" | "insight" | "warning" | "success";
  title: string;
  description: string;
  impact?: string;
}

interface ActionData {
  action: string;
  expected_result: string;
  priority: "high" | "medium" | "low";
}

// ==================== Color Palettes ====================

const CHART_COLORS = [
  "#34d399", // emerald
  "#22d3ee", // cyan
  "#a78bfa", // violet
  "#f472b6", // pink
  "#fbbf24", // amber
  "#60a5fa", // blue
];

const PRIORITY_COLORS = {
  high: "bg-red-500/20 text-red-300 border-red-500/30",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  low: "bg-blue-500/20 text-blue-300 border-blue-500/30",
};

// ==================== Parsing Functions ====================

function extractKPIs(text: string): KPIData[] {
  const kpis: KPIData[] = [];
  
  // Pattern: "Revenue: ₹1,50,000 (+12%)" or "Total Sales: 500 units"
  const kpiPatterns = [
    /(?:^|\n)\s*[-•]\s*\*\*([^:*]+)\*\*:\s*([₹$]?[\d,]+(?:\.\d+)?)\s*(?:(\([+-]?\d+(?:\.\d+)?%\)))?/gm,
    /(?:^|\n)\s*\*\*([^:*]+)\*\*:\s*([₹$]?[\d,]+(?:\.\d+)?)\s*(?:(\([+-]?\d+(?:\.\d+)?%\)))?/gm,
    /(?:^|\n)\s*([A-Za-z\s]+):\s*₹([\d,]+(?:\.\d+)?)\s*(?:\(([+-]?\d+(?:\.\d+)?%)\))?/gm,
  ];

  for (const pattern of kpiPatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const label = match[1]?.trim();
      const value = match[2]?.trim();
      const changeStr = match[3]?.replace(/[()%]/g, "");
      
      if (label && value) {
        const change = changeStr ? parseFloat(changeStr) : undefined;
        kpis.push({
          label,
          value,
          change,
          trend: change ? (change > 0 ? "up" : change < 0 ? "down" : "neutral") : undefined,
        });
      }
    }
  }

  return kpis;
}

function extractTable(text: string): TableData | null {
  // Look for markdown tables
  const tableMatch = text.match(/\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)/);
  
  if (tableMatch) {
    const headerLine = tableMatch[1];
    const bodyLines = tableMatch[2].trim().split("\n");
    
    const headers = headerLine.split("|").map(h => h.trim()).filter(Boolean);
    const rows = bodyLines.map(line => 
      line.split("|").map(cell => cell.trim()).filter(Boolean)
    );
    
    if (headers.length > 0 && rows.length > 0) {
      return { headers, rows };
    }
  }
  
  return null;
}

function extractTasks(text: string): TaskData[] {
  const tasks: TaskData[] = [];
  
  // Pattern: [TASK: description] or **Task:** description
  const taskPatterns = [
    /\[TASK:\s*([^\]]+)\]/gi,
    /\*\*Task\*\*:\s*([^\n]+)/gi,
    /(?:^|\n)\s*[-•]\s*\*\*Action\*\*:\s*([^\n]+)/gim,
  ];

  let taskId = 1;
  for (const pattern of taskPatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const title = match[1]?.trim();
      if (title) {
        // Detect priority from keywords
        let priority: "high" | "medium" | "low" = "medium";
        if (/urgent|critical|immediate/i.test(title)) priority = "high";
        if (/low|minor|later/i.test(title)) priority = "low";
        
        tasks.push({
          id: `task_${taskId++}`,
          title,
          priority,
        });
      }
    }
  }

  return tasks;
}

function extractFindings(text: string): FindingData[] {
  const findings: FindingData[] = [];
  
  // Look for structured findings
  const findingPatterns = [
    { pattern: /⚠️\s*\*\*([^*]+)\*\*:?\s*([^\n]+)/gi, type: "warning" as const },
    { pattern: /🚨\s*\*\*([^*]+)\*\*:?\s*([^\n]+)/gi, type: "issue" as const },
    { pattern: /✅\s*\*\*([^*]+)\*\*:?\s*([^\n]+)/gi, type: "success" as const },
    { pattern: /💡\s*\*\*([^*]+)\*\*:?\s*([^\n]+)/gi, type: "insight" as const },
    { pattern: /\*\*Finding\*\*:\s*([^\n]+)/gi, type: "insight" as const },
    { pattern: /\*\*Issue\*\*:\s*([^\n]+)/gi, type: "issue" as const },
  ];

  for (const { pattern, type } of findingPatterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      findings.push({
        type,
        title: match[1]?.trim() || type,
        description: match[2]?.trim() || match[1]?.trim() || "",
      });
    }
  }

  return findings;
}

function extractChartData(text: string): ChartData | null {
  // Look for data that could be charted (series of numbers with labels)
  const dataPattern = /(?:^|\n)(?:[-•]\s*)?([A-Za-z\s]+):\s*([\d,]+(?:\.\d+)?)/gm;
  const matches: { label: string; value: number }[] = [];
  
  let match;
  while ((match = dataPattern.exec(text)) !== null) {
    const label = match[1]?.trim();
    const valueStr = match[2]?.replace(/,/g, "");
    const value = parseFloat(valueStr);
    
    if (label && !isNaN(value)) {
      matches.push({ label, value });
    }
  }

  // Only create chart if we have 3+ data points
  if (matches.length >= 3) {
    return {
      type: "bar",
      title: "Data Summary",
      data: matches,
      xKey: "label",
      yKey: "value",
    };
  }

  return null;
}

// ==================== Render Components ====================

function KPICard({ kpi }: { kpi: KPIData }) {
  const TrendIcon = kpi.trend === "up" ? TrendingUp : kpi.trend === "down" ? TrendingDown : Minus;
  const trendColor = kpi.trend === "up" ? "text-emerald-400" : kpi.trend === "down" ? "text-red-400" : "text-zinc-400";

  return (
    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 p-4">
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">{kpi.label}</div>
      <div className="mt-1 flex items-end justify-between">
        <span className="text-2xl font-bold text-white">{kpi.value}</span>
        {kpi.change !== undefined && (
          <div className={`flex items-center gap-1 text-sm ${trendColor}`}>
            <TrendIcon size={16} />
            <span>{kpi.change > 0 ? "+" : ""}{kpi.change}%</span>
          </div>
        )}
      </div>
    </div>
  );
}

function DataTable({ data }: { data: TableData }) {
  return (
    <div className="overflow-hidden rounded-xl border border-white/10">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/10 bg-black/30">
              {data.headers.map((header, i) => (
                <th key={i} className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {data.rows.map((row, i) => (
              <tr key={i} className="hover:bg-white/5">
                {row.map((cell, j) => (
                  <td key={j} className="px-4 py-2 text-sm text-zinc-300">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DataChart({ chart }: { chart: ChartData }) {
  const renderChart = () => {
    switch (chart.type) {
      case "line":
        return (
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
            <Line type="monotone" dataKey={chart.yKey as string} stroke="#34d399" strokeWidth={2} dot={{ fill: "#34d399" }} />
          </LineChart>
        );
      
      case "bar":
        return (
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
            <Bar dataKey={chart.yKey as string} fill="#34d399" radius={[4, 4, 0, 0]} />
          </BarChart>
        );
      
      case "pie":
        return (
          <PieChart>
            <Pie
              data={chart.data}
              dataKey={chart.yKey as string}
              nameKey={chart.xKey}
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name }) => name}
            >
              {chart.data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
          </PieChart>
        );
      
      case "area":
        return (
          <AreaChart data={chart.data}>
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
            <Area type="monotone" dataKey={chart.yKey as string} stroke="#34d399" fill="rgba(52,211,153,0.2)" />
          </AreaChart>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="rounded-xl border border-white/10 bg-black/30 p-4">
      {chart.title && (
        <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-emerald-200">
          {chart.title}
        </div>
      )}
      <ResponsiveContainer width="100%" height={200}>
        {renderChart() as any}
      </ResponsiveContainer>
    </div>
  );
}

function TaskCard({ task, onAssign }: { task: TaskData; onAssign?: (task: TaskData) => void }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-white/10 bg-gradient-to-r from-violet-500/10 to-purple-500/5 p-4">
      <div className="flex items-center gap-3">
        <Target size={18} className="text-violet-400" />
        <div>
          <div className="font-medium text-white">{task.title}</div>
          {task.assignee && <div className="text-xs text-zinc-500">Assigned to: {task.assignee}</div>}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[task.priority]}`}>
          {task.priority}
        </span>
        {onAssign && (
          <button
            onClick={() => onAssign(task)}
            className="rounded-lg bg-violet-500/20 px-3 py-1.5 text-xs font-medium text-violet-300 transition hover:bg-violet-500/30"
          >
            Assign Task
          </button>
        )}
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: FindingData }) {
  const icons = {
    issue: AlertTriangle,
    warning: AlertTriangle,
    success: CheckCircle,
    insight: Info,
  };
  const colors = {
    issue: "text-red-400 bg-red-500/20 border-red-500/30",
    warning: "text-amber-400 bg-amber-500/20 border-amber-500/30",
    success: "text-emerald-400 bg-emerald-500/20 border-emerald-500/30",
    insight: "text-blue-400 bg-blue-500/20 border-blue-500/30",
  };

  const Icon = icons[finding.type];
  const colorClass = colors[finding.type];

  return (
    <div className={`rounded-xl border p-4 ${colorClass}`}>
      <div className="flex items-start gap-3">
        <Icon size={18} className="mt-0.5 shrink-0" />
        <div>
          <div className="font-semibold">{finding.title}</div>
          <div className="mt-1 text-sm opacity-80">{finding.description}</div>
          {finding.impact && (
            <div className="mt-2 text-xs opacity-60">Impact: {finding.impact}</div>
          )}
        </div>
      </div>
    </div>
  );
}

// ==================== Main Component ====================

interface AIResponseFormatterProps {
  content: string;
  onTaskAssign?: (task: TaskData) => void;
}

export default function AIResponseFormatter({ content, onTaskAssign }: AIResponseFormatterProps) {
  const parsed = useMemo(() => {
    const kpis = extractKPIs(content);
    const table = extractTable(content);
    const tasks = extractTasks(content);
    const findings = extractFindings(content);
    const chart = extractChartData(content);

    // Remove extracted structured content from text for cleaner display
    let cleanText = content;
    
    // Don't clean text for now - show both structured and raw
    // This ensures nothing is lost while adding visualizations

    return {
      kpis,
      table,
      tasks,
      findings,
      chart,
      text: cleanText,
    };
  }, [content]);

  const hasStructuredContent = 
    parsed.kpis.length > 0 || 
    parsed.table || 
    parsed.tasks.length > 0 || 
    parsed.findings.length > 0 ||
    parsed.chart;

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      {parsed.kpis.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {parsed.kpis.slice(0, 6).map((kpi, i) => (
            <KPICard key={i} kpi={kpi} />
          ))}
        </div>
      )}

      {/* Chart */}
      {parsed.chart && (
        <DataChart chart={parsed.chart} />
      )}

      {/* Table */}
      {parsed.table && (
        <DataTable data={parsed.table} />
      )}

      {/* Findings */}
      {parsed.findings.length > 0 && (
        <div className="space-y-2">
          {parsed.findings.map((finding, i) => (
            <FindingCard key={i} finding={finding} />
          ))}
        </div>
      )}

      {/* Tasks */}
      {parsed.tasks.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-violet-200">
            📋 Action Items
          </div>
          {parsed.tasks.map((task) => (
            <TaskCard key={task.id} task={task} onAssign={onTaskAssign} />
          ))}
        </div>
      )}

      {/* Original Text (for context) */}
      {!hasStructuredContent && (
        <div className="whitespace-pre-wrap text-sm leading-relaxed">{content}</div>
      )}
    </div>
  );
}

// ==================== Export Types ====================

export type { TaskData, KPIData, FindingData, ChartData, TableData };
