"use client";

import SmartMarkdown from "@/components/SmartMarkdown";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type TitanSuggestedTask = {
  title: string;
  assignee?: string;
  priority?: "High" | "Medium" | "Low" | string;
  deadline?: string;
};

export type TitanChartDatum = {
  name?: string;
  label?: string;
  value?: number | string;
  color?: string;
  [key: string]: unknown;
};

export type TitanVisualWidget = {
  type: "bar" | "line" | "pie" | "kpi_card";
  title?: string;
  data: TitanChartDatum[];
};

export type TitanEnvelope = {
  thought_process?: string;
  message?: string;
  visual_widget?: TitanVisualWidget | null;
  suggested_tasks?: TitanSuggestedTask[];
  next_questions?: string[];
};

const CHART_COLORS = ["#34d399", "#22d3ee", "#a78bfa", "#f472b6", "#fbbf24", "#60a5fa"];

function safeParseEnvelope(text: string): TitanEnvelope | null {
  if (!text) return null;
  const raw = String(text).trim();
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) return null;
  const candidate = raw.slice(start, end + 1);
  try {
    const obj = JSON.parse(candidate);
    return obj && typeof obj === "object" ? (obj as TitanEnvelope) : null;
  } catch {
    return null;
  }
}

function KpiCard({ item }: { item: TitanChartDatum }) {
  const label = String(item.label ?? item.name ?? "KPI");
  const value = item.value ?? item.amount ?? item.metric ?? "";
  return (
    <div className="rounded-xl border border-white/10 bg-gradient-to-br from-emerald-500/10 to-cyan-500/5 p-4">
      <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">{label}</div>
      <div className="mt-1 text-2xl font-bold text-white">{String(value)}</div>
    </div>
  );
}

function getDatumColor(datum: TitanChartDatum, idx: number): string {
  if (typeof datum.color === "string" && datum.color) return datum.color;
  return CHART_COLORS[idx % CHART_COLORS.length];
}

function VisualWidget({ widget }: { widget: TitanVisualWidget }) {
  const title = widget.title ? (
    <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-emerald-200">{widget.title}</div>
  ) : null;

  if (widget.type === "kpi_card") {
    return (
      <div className="rounded-xl border border-white/10 bg-black/30 p-4">
        {title}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(widget.data || []).slice(0, 6).map((d, idx) => (
            <KpiCard key={idx} item={d} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/10 bg-black/30 p-4">
      {title}
      <ResponsiveContainer width="100%" height={220}>
        {widget.type === "bar" ? (
          <BarChart data={widget.data || []}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
            <Bar dataKey="value" fill="#34d399" radius={[4, 4, 0, 0]}>
              {(widget.data || []).map((d, idx) => (
                <Cell key={idx} fill={getDatumColor(d, idx)} />
              ))}
            </Bar>
          </BarChart>
        ) : widget.type === "line" ? (
          <LineChart data={widget.data || []}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <YAxis stroke="rgba(255,255,255,0.5)" style={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
            <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={2} dot={{ fill: "#22d3ee" }} />
          </LineChart>
        ) : (
          <PieChart>
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(0,0,0,0.9)",
                border: "1px solid rgba(52,211,153,0.3)",
                borderRadius: "8px",
              }}
            />
            <Pie data={widget.data || []} dataKey="value" nameKey="name" outerRadius={80}>
              {(widget.data || []).map((_, idx) => (
                <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

function SuggestedTaskCard({ task, onAssign }: { task: TitanSuggestedTask; onAssign?: (task: TitanSuggestedTask) => void }) {
  const priority = String(task.priority || "Medium");
  const cls =
    priority.toLowerCase() === "high"
      ? "bg-red-500/20 text-red-300 border-red-500/30"
      : priority.toLowerCase() === "low"
        ? "bg-blue-500/20 text-blue-300 border-blue-500/30"
        : "bg-amber-500/20 text-amber-300 border-amber-500/30";

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-gradient-to-r from-violet-500/10 to-purple-500/5 p-4">
      <div className="min-w-0">
        <div className="truncate font-medium text-white">{task.title}</div>
        <div className="mt-1 text-xs text-zinc-400">
          {task.assignee ? `Owner: ${task.assignee}` : "Owner: (not set)"}
          {task.deadline ? ` • Deadline: ${task.deadline}` : ""}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}>{priority}</span>
        {onAssign ? (
          <button
            type="button"
            onClick={() => onAssign(task)}
            className="rounded-lg bg-violet-500/20 px-3 py-1.5 text-xs font-medium text-violet-300 transition hover:bg-violet-500/30"
          >
            Assign
          </button>
        ) : null}
      </div>
    </div>
  );
}

export default function VisualResponse({
  content,
  envelope,
  onTaskAssign,
}: {
  content: string;
  envelope?: TitanEnvelope | null;
  onTaskAssign?: (task: TitanSuggestedTask) => void;
}) {
  const parsed = envelope ?? safeParseEnvelope(content);

  if (!parsed) {
    return <SmartMarkdown content={content || ""} />;
  }

  return (
    <div className="space-y-4">
      <SmartMarkdown content={String(parsed.message || "")} />

      {parsed.visual_widget ? <VisualWidget widget={parsed.visual_widget} /> : null}

      {Array.isArray(parsed.suggested_tasks) && parsed.suggested_tasks.length > 0 ? (
        <div className="space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-violet-200">Action Items</div>
          {parsed.suggested_tasks.map((t, idx) => (
            <SuggestedTaskCard key={idx} task={t} onAssign={onTaskAssign} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
