"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  ToggleLeft, 
  ToggleRight, 
  RefreshCw, 
  Search,
  Beaker,
  Crown,
  Zap,
  Shield
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface Feature {
  feature_id: string;
  name: string;
  description: string;
  tiers: string[];
  category: string;
  is_beta: boolean;
  rollout_percentage: number;
}

interface FeaturesByCategory {
  [category: string]: string[];
}

export default function FeaturesPage() {
  const [features, setFeatures] = useState<Feature[]>([]);
  const [byCategory, setByCategory] = useState<FeaturesByCategory>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");

  const fetchFeatures = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/master/features`);
      if (res.ok) {
        const data = await res.json();
        setFeatures(data.features || []);
        setByCategory(data.by_category || {});
      }
    } catch (error) {
      console.error("Failed to fetch features:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeatures();
  }, []);

  const categories = Object.keys(byCategory);
  
  const filteredFeatures = features.filter(f => {
    const matchesSearch = f.name.toLowerCase().includes(search.toLowerCase()) ||
                         f.description.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !selectedCategory || f.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case "enterprise": return "bg-violet-500/20 text-violet-300 border-violet-500/30";
      case "pro": return "bg-cyan-500/20 text-cyan-300 border-cyan-500/30";
      default: return "bg-zinc-500/20 text-zinc-300 border-zinc-500/30";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "ai": return Zap;
      case "reporting": return Crown;
      case "integration": return Shield;
      default: return ToggleLeft;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Feature Flags</h2>
          <p className="text-sm text-zinc-400">Manage features across subscription tiers</p>
        </div>
        <button
          onClick={fetchFeatures}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/10"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Tier Legend */}
      <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
        <span className="text-sm font-medium text-zinc-400">Subscription Tiers:</span>
        <div className="flex items-center gap-2">
          <span className="rounded-full border bg-zinc-500/20 text-zinc-300 border-zinc-500/30 px-3 py-1 text-xs font-medium">
            Free
          </span>
          <span className="text-xs text-zinc-500">Basic features</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30 px-3 py-1 text-xs font-medium">
            Pro
          </span>
          <span className="text-xs text-zinc-500">Advanced features</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border bg-violet-500/20 text-violet-300 border-violet-500/30 px-3 py-1 text-xs font-medium">
            Enterprise
          </span>
          <span className="text-xs text-zinc-500">Full access</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search features..."
            className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50"
          />
        </div>
        
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
        >
          <option value="">All Categories</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Features Grid */}
      {loading ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
          <RefreshCw size={24} className="mx-auto animate-spin text-violet-400" />
          <p className="mt-3 text-sm text-zinc-400">Loading features...</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredFeatures.map((feature) => {
            const Icon = getCategoryIcon(feature.category);
            return (
              <motion.div
                key={feature.feature_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 transition hover:border-violet-500/30"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-xl bg-violet-500/20 p-2">
                      <Icon size={18} className="text-violet-400" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{feature.name}</h4>
                      <p className="text-xs text-zinc-500">{feature.category}</p>
                    </div>
                  </div>
                  {feature.is_beta && (
                    <span className="flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-medium text-amber-300">
                      <Beaker size={10} />
                      Beta
                    </span>
                  )}
                </div>

                <p className="mt-3 text-sm text-zinc-400 line-clamp-2">{feature.description}</p>

                <div className="mt-4 flex flex-wrap gap-1">
                  {feature.tiers.map(tier => (
                    <span key={tier} className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${getTierBadge(tier)}`}>
                      {tier}
                    </span>
                  ))}
                </div>

                {feature.rollout_percentage < 100 && (
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-zinc-500">Rollout</span>
                      <span className="text-zinc-300">{feature.rollout_percentage}%</span>
                    </div>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-zinc-800">
                      <div 
                        className="h-full rounded-full bg-violet-500"
                        style={{ width: `${feature.rollout_percentage}%` }}
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
          <div className="text-2xl font-bold text-white">{features.length}</div>
          <div className="text-sm text-zinc-400">Total Features</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
          <div className="text-2xl font-bold text-amber-400">{features.filter(f => f.is_beta).length}</div>
          <div className="text-sm text-zinc-400">Beta Features</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
          <div className="text-2xl font-bold text-cyan-400">{features.filter(f => f.tiers.includes('pro')).length}</div>
          <div className="text-sm text-zinc-400">Pro Features</div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
          <div className="text-2xl font-bold text-violet-400">{features.filter(f => f.tiers.includes('enterprise') && !f.tiers.includes('pro')).length}</div>
          <div className="text-sm text-zinc-400">Enterprise Only</div>
        </div>
      </div>
    </div>
  );
}
