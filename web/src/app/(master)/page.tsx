"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  Users, 
  DollarSign, 
  AlertTriangle, 
  TrendingUp,
  Activity,
  Brain,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface OverviewData {
  total_tenants: number;
  active_tenants: number;
  total_cost_today: number;
  total_cost_week: number;
  active_alerts: number;
  critical_alerts: number;
  system_status: string;
  ai_insights_pending: number;
}

interface TopUser {
  tenant_id: string;
  total_cost: number;
  total_tokens: number;
  total_messages: number;
}

interface Alert {
  alert_id: string;
  tenant_id: string | null;
  severity: string;
  title: string;
  created_at: string;
}

interface Insight {
  insight_id: string;
  type: string;
  priority: string;
  tenant_id: string | null;
  title: string;
  description: string;
}

function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend,
  color = "violet" 
}: { 
  title: string; 
  value: string | number; 
  subtitle?: string;
  icon: React.ElementType;
  trend?: { value: number; positive: boolean };
  color?: "violet" | "emerald" | "amber" | "red";
}) {
  const colors = {
    violet: "from-violet-500/20 to-purple-500/20 border-violet-500/30",
    emerald: "from-emerald-500/20 to-cyan-500/20 border-emerald-500/30",
    amber: "from-amber-500/20 to-orange-500/20 border-amber-500/30",
    red: "from-red-500/20 to-rose-500/20 border-red-500/30",
  };

  const iconColors = {
    violet: "text-violet-400",
    emerald: "text-emerald-400",
    amber: "text-amber-400",
    red: "text-red-400",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border bg-gradient-to-br p-5 ${colors[color]}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-zinc-400">{title}</div>
          <div className="mt-2 text-3xl font-bold text-white">{value}</div>
          {subtitle && <div className="mt-1 text-sm text-zinc-400">{subtitle}</div>}
          {trend && (
            <div className={`mt-2 flex items-center gap-1 text-xs ${trend.positive ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend.positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              <span>{Math.abs(trend.value)}% vs last week</span>
            </div>
          )}
        </div>
        <div className={`rounded-xl bg-black/20 p-3 ${iconColors[color]}`}>
          <Icon size={24} />
        </div>
      </div>
    </motion.div>
  );
}

export default function MasterOverviewPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewRes, usageRes, alertsRes, insightsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/master/overview`),
        fetch(`${API_BASE_URL}/api/v1/master/usage?days=7`),
        fetch(`${API_BASE_URL}/api/v1/master/alerts?limit=5`),
        fetch(`${API_BASE_URL}/api/v1/master/ai/insights?unacknowledged_only=true&limit=5`),
      ]);

      if (overviewRes.ok) {
        setOverview(await overviewRes.json());
      }
      if (usageRes.ok) {
        const usageData = await usageRes.json();
        setTopUsers(usageData.top_users || []);
      }
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(alertsData.alerts || []);
      }
      if (insightsRes.ok) {
        const insightsData = await insightsRes.json();
        setInsights(insightsData.insights || []);
      }
    } catch (error) {
      console.error("Failed to fetch master data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatCurrency = (value: number) => {
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">System Overview</h2>
          <p className="text-sm text-zinc-400">Real-time monitoring of all tenants and resources</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm font-medium text-violet-200 transition hover:bg-violet-500/20 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Tenants"
          value={overview?.total_tenants ?? 0}
          subtitle={`${overview?.active_tenants ?? 0} active`}
          icon={Users}
          color="violet"
        />
        <StatCard
          title="Today's Cost"
          value={formatCurrency(overview?.total_cost_today ?? 0)}
          subtitle={`${formatCurrency(overview?.total_cost_week ?? 0)} this week`}
          icon={DollarSign}
          color="emerald"
        />
        <StatCard
          title="Active Alerts"
          value={overview?.active_alerts ?? 0}
          subtitle={`${overview?.critical_alerts ?? 0} critical`}
          icon={AlertTriangle}
          color={overview?.critical_alerts ? "red" : "amber"}
        />
        <StatCard
          title="AI Insights"
          value={overview?.ai_insights_pending ?? 0}
          subtitle="Pending review"
          icon={Brain}
          color="violet"
        />
      </div>

      {/* Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Top Users */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-5"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Top Users by Cost</h3>
            <span className="text-xs text-zinc-500">Last 7 days</span>
          </div>
          <div className="space-y-3">
            {topUsers.length === 0 ? (
              <div className="py-8 text-center text-sm text-zinc-500">No usage data available</div>
            ) : (
              topUsers.slice(0, 5).map((user, idx) => (
                <div key={user.tenant_id} className="flex items-center justify-between rounded-xl bg-black/20 px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-violet-500/20 text-xs font-bold text-violet-300">
                      {idx + 1}
                    </span>
                    <div>
                      <div className="font-medium text-white">{user.tenant_id}</div>
                      <div className="text-xs text-zinc-500">{user.total_messages} messages</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-emerald-400">{formatCurrency(user.total_cost)}</div>
                    <div className="text-xs text-zinc-500">{user.total_tokens?.toLocaleString()} tokens</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* Recent Alerts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-5"
        >
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Recent Alerts</h3>
            <a href="/master/alerts" className="text-xs text-violet-400 hover:underline">View all</a>
          </div>
          <div className="space-y-3">
            {alerts.length === 0 ? (
              <div className="py-8 text-center text-sm text-zinc-500">No active alerts</div>
            ) : (
              alerts.map((alert) => (
                <div key={alert.alert_id} className="flex items-start gap-3 rounded-xl bg-black/20 px-4 py-3">
                  <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                    alert.severity === 'critical' ? 'bg-red-500' :
                    alert.severity === 'error' ? 'bg-orange-500' :
                    alert.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                  }`} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-medium text-white">{alert.title}</div>
                    <div className="text-xs text-zinc-500">
                      {alert.tenant_id || 'System'} • {new Date(alert.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        {/* AI Insights */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-5 lg:col-span-2"
        >
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain size={20} className="text-violet-400" />
              <h3 className="text-lg font-semibold text-white">AI Watchdog Insights</h3>
            </div>
            <a href="/master/ai-watchdog" className="text-xs text-violet-400 hover:underline">View all</a>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {insights.length === 0 ? (
              <div className="col-span-2 py-8 text-center text-sm text-zinc-500">No pending insights</div>
            ) : (
              insights.map((insight) => (
                <div key={insight.insight_id} className="rounded-xl bg-black/20 p-4">
                  <div className="mb-2 flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                      insight.priority === 'urgent' ? 'bg-red-500/20 text-red-300' :
                      insight.priority === 'high' ? 'bg-orange-500/20 text-orange-300' :
                      insight.priority === 'medium' ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300'
                    }`}>
                      {insight.priority}
                    </span>
                    <span className="rounded-full bg-violet-500/20 px-2 py-0.5 text-[10px] font-medium text-violet-300">
                      {insight.type.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="font-medium text-white">{insight.title}</div>
                  <div className="mt-1 text-xs text-zinc-400 line-clamp-2">{insight.description}</div>
                  {insight.tenant_id && (
                    <div className="mt-2 text-xs text-zinc-500">Tenant: {insight.tenant_id}</div>
                  )}
                </div>
              ))
            )}
          </div>
        </motion.div>
      </div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-5"
      >
        <h3 className="mb-4 text-lg font-semibold text-white">System Status</h3>
        <div className="grid gap-4 md:grid-cols-4">
          <div className="flex items-center gap-3 rounded-xl bg-black/20 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(52,211,153,0.5)]" />
            <div>
              <div className="text-sm font-medium text-white">API Server</div>
              <div className="text-xs text-emerald-400">Operational</div>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl bg-black/20 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(52,211,153,0.5)]" />
            <div>
              <div className="text-sm font-medium text-white">BigQuery</div>
              <div className="text-xs text-emerald-400">Connected</div>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl bg-black/20 px-4 py-3">
            <span className="h-3 w-3 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(52,211,153,0.5)]" />
            <div>
              <div className="text-sm font-medium text-white">Gemini AI</div>
              <div className="text-xs text-emerald-400">Active</div>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-xl bg-black/20 px-4 py-3">
            <span className={`h-3 w-3 rounded-full ${
              overview?.system_status === 'healthy' ? 'bg-emerald-500 shadow-[0_0_10px_rgba(52,211,153,0.5)]' :
              overview?.system_status === 'warning' ? 'bg-amber-500' : 'bg-red-500'
            }`} />
            <div>
              <div className="text-sm font-medium text-white">Overall</div>
              <div className={`text-xs ${
                overview?.system_status === 'healthy' ? 'text-emerald-400' :
                overview?.system_status === 'warning' ? 'text-amber-400' : 'text-red-400'
              }`}>
                {overview?.system_status || 'Unknown'}
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
