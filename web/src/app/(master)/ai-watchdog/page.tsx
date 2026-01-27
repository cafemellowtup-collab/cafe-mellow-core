"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  Brain, 
  RefreshCw, 
  Check, 
  AlertTriangle,
  TrendingDown,
  DollarSign,
  UserX,
  Lightbulb,
  Play,
  Filter
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface Insight {
  insight_id: string;
  type: string;
  priority: string;
  tenant_id: string | null;
  title: string;
  description: string;
  recommendation: string;
  data: Record<string, any>;
  created_at: string;
  acknowledged: boolean;
}

interface Digest {
  date: string;
  total_insights: number;
  by_priority: Record<string, number>;
  by_type: Record<string, number>;
  urgent_items: Array<{ tenant_id: string; title: string; type: string }>;
  high_priority_items: Array<{ tenant_id: string; title: string; type: string }>;
}

export default function AIWatchdogPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [filter, setFilter] = useState({ type: "", priority: "", unacknowledged: true });

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.type) params.append("insight_type", filter.type);
      if (filter.priority) params.append("priority", filter.priority);
      if (filter.unacknowledged) params.append("unacknowledged_only", "true");

      const [insightsRes, digestRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/master/ai/insights?${params.toString()}`),
        fetch(`${API_BASE_URL}/api/v1/master/ai/digest`),
      ]);

      if (insightsRes.ok) {
        const data = await insightsRes.json();
        setInsights(data.insights || []);
      }
      if (digestRes.ok) {
        setDigest(await digestRes.json());
      }
    } catch (error) {
      console.error("Failed to fetch AI data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  const runAnalysis = async () => {
    setRunningAnalysis(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/master/ai/run-analysis`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Analysis complete! ${data.insights_generated} new insights generated.`);
        fetchData();
      }
    } catch (error) {
      console.error("Failed to run analysis:", error);
    } finally {
      setRunningAnalysis(false);
    }
  };

  const acknowledgeInsight = async (insightId: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/master/ai/insights/${insightId}/acknowledge`, {
        method: "POST",
      });
      fetchData();
    } catch (error) {
      console.error("Failed to acknowledge insight:", error);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "usage_anomaly": return AlertTriangle;
      case "churn_risk": return UserX;
      case "engagement_drop": return TrendingDown;
      case "cost_alert": return DollarSign;
      case "feature_suggestion": return Lightbulb;
      default: return Brain;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "usage_anomaly": return "text-amber-400 bg-amber-500/20";
      case "churn_risk": return "text-red-400 bg-red-500/20";
      case "engagement_drop": return "text-orange-400 bg-orange-500/20";
      case "cost_alert": return "text-emerald-400 bg-emerald-500/20";
      case "feature_suggestion": return "text-blue-400 bg-blue-500/20";
      default: return "text-violet-400 bg-violet-500/20";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent": return "bg-red-500/20 text-red-300 border-red-500/30";
      case "high": return "bg-orange-500/20 text-orange-300 border-orange-500/30";
      case "medium": return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      default: return "bg-blue-500/20 text-blue-300 border-blue-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">AI Watchdog</h2>
          <p className="text-sm text-zinc-400">Proactive monitoring and intelligent insights</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/10"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
          <button
            onClick={runAnalysis}
            disabled={runningAnalysis}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition hover:shadow-violet-500/40 disabled:opacity-50"
          >
            <Play size={16} className={runningAnalysis ? "animate-pulse" : ""} />
            {runningAnalysis ? "Analyzing..." : "Run Analysis"}
          </button>
        </div>
      </div>

      {/* Daily Digest */}
      {digest && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-violet-500/20 bg-gradient-to-br from-violet-500/10 to-purple-500/10 p-6"
        >
          <div className="flex items-center gap-3 mb-4">
            <div className="rounded-xl bg-violet-500/20 p-2">
              <Brain size={24} className="text-violet-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Daily AI Digest</h3>
              <p className="text-sm text-zinc-400">{digest.date}</p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-xl bg-black/20 p-4">
              <div className="text-2xl font-bold text-white">{digest.total_insights}</div>
              <div className="text-sm text-zinc-400">Total Insights</div>
            </div>
            <div className="rounded-xl bg-black/20 p-4">
              <div className="text-2xl font-bold text-red-400">{digest.by_priority?.urgent || 0}</div>
              <div className="text-sm text-zinc-400">Urgent</div>
            </div>
            <div className="rounded-xl bg-black/20 p-4">
              <div className="text-2xl font-bold text-orange-400">{digest.by_priority?.high || 0}</div>
              <div className="text-sm text-zinc-400">High Priority</div>
            </div>
            <div className="rounded-xl bg-black/20 p-4">
              <div className="text-2xl font-bold text-amber-400">{digest.by_priority?.medium || 0}</div>
              <div className="text-sm text-zinc-400">Medium</div>
            </div>
          </div>

          {digest.urgent_items && digest.urgent_items.length > 0 && (
            <div className="mt-4 rounded-xl bg-red-500/10 border border-red-500/20 p-4">
              <div className="text-sm font-semibold text-red-300 mb-2">⚠️ Urgent Items Requiring Attention</div>
              <div className="space-y-2">
                {digest.urgent_items.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-zinc-300">
                    <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                    <span>{item.title}</span>
                    <span className="text-zinc-500">({item.tenant_id || 'System'})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={filter.type}
          onChange={(e) => setFilter({ ...filter, type: e.target.value })}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
        >
          <option value="">All Types</option>
          <option value="usage_anomaly">Usage Anomaly</option>
          <option value="churn_risk">Churn Risk</option>
          <option value="engagement_drop">Engagement Drop</option>
          <option value="cost_alert">Cost Alert</option>
          <option value="feature_suggestion">Feature Suggestion</option>
        </select>

        <select
          value={filter.priority}
          onChange={(e) => setFilter({ ...filter, priority: e.target.value })}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
        >
          <option value="">All Priorities</option>
          <option value="urgent">Urgent</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={filter.unacknowledged}
            onChange={(e) => setFilter({ ...filter, unacknowledged: e.target.checked })}
            className="rounded border-white/20 bg-white/5"
          />
          Unacknowledged only
        </label>
      </div>

      {/* Insights List */}
      <div className="space-y-4">
        {loading ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
            <RefreshCw size={24} className="mx-auto animate-spin text-violet-400" />
            <p className="mt-3 text-sm text-zinc-400">Loading insights...</p>
          </div>
        ) : insights.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
            <Brain size={32} className="mx-auto text-zinc-600" />
            <p className="mt-3 text-sm text-zinc-400">No insights found</p>
            <p className="text-xs text-zinc-500">Run an analysis to generate new insights</p>
          </div>
        ) : (
          insights.map((insight) => {
            const Icon = getTypeIcon(insight.type);
            return (
              <motion.div
                key={insight.insight_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-white/10 bg-white/5 p-5"
              >
                <div className="flex items-start gap-4">
                  <div className={`rounded-xl p-3 ${getTypeColor(insight.type)}`}>
                    <Icon size={20} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${getPriorityColor(insight.priority)}`}>
                        {insight.priority}
                      </span>
                      <span className="rounded-full bg-zinc-700/50 px-2.5 py-0.5 text-xs text-zinc-300">
                        {insight.type.replace(/_/g, ' ')}
                      </span>
                      {insight.tenant_id && (
                        <span className="text-xs text-zinc-500">
                          Tenant: {insight.tenant_id}
                        </span>
                      )}
                    </div>
                    
                    <h4 className="text-lg font-semibold text-white">{insight.title}</h4>
                    <p className="mt-1 text-sm text-zinc-400">{insight.description}</p>
                    
                    <div className="mt-3 rounded-xl bg-violet-500/10 border border-violet-500/20 p-3">
                      <div className="text-xs font-semibold text-violet-300 mb-1">💡 Recommendation</div>
                      <p className="text-sm text-zinc-300">{insight.recommendation}</p>
                    </div>

                    {insight.data && Object.keys(insight.data).length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {Object.entries(insight.data).map(([key, value]) => (
                          <span key={key} className="rounded-lg bg-black/20 px-2 py-1 text-xs text-zinc-400">
                            {key}: <span className="text-zinc-200">{typeof value === 'number' ? value.toLocaleString() : String(value)}</span>
                          </span>
                        ))}
                      </div>
                    )}

                    <div className="mt-4 flex items-center justify-between">
                      <span className="text-xs text-zinc-500">
                        {new Date(insight.created_at).toLocaleString()}
                      </span>
                      
                      {!insight.acknowledged && (
                        <button
                          onClick={() => acknowledgeInsight(insight.insight_id)}
                          className="flex items-center gap-2 rounded-lg bg-emerald-500/20 px-3 py-1.5 text-xs font-medium text-emerald-300 transition hover:bg-emerald-500/30"
                        >
                          <Check size={14} />
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
