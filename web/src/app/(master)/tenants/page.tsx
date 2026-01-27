"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  Search, 
  Plus, 
  MoreVertical, 
  Eye, 
  Pause, 
  Play, 
  Settings,
  RefreshCw,
  Filter,
  ChevronDown
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";

interface Tenant {
  tenant_id: string;
  name: string;
  email: string;
  plan: string;
  status: string;
  created_at: string;
  last_activity: string | null;
  health_score: number;
}

interface NewTenantForm {
  name: string;
  email: string;
  phone: string;
  plan: string;
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [planFilter, setPlanFilter] = useState<string>("");
  const [showNewTenant, setShowNewTenant] = useState(false);
  const [newTenant, setNewTenant] = useState<NewTenantForm>({ name: "", email: "", phone: "", plan: "free" });
  const [creating, setCreating] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<string | null>(null);

  const fetchTenants = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append("status", statusFilter);
      if (planFilter) params.append("plan", planFilter);
      
      const res = await fetch(`${API_BASE_URL}/api/v1/master/tenants?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setTenants(data.tenants || []);
      }
    } catch (error) {
      console.error("Failed to fetch tenants:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenants();
  }, [statusFilter, planFilter]);

  const createTenant = async () => {
    if (!newTenant.name || !newTenant.email) return;
    
    setCreating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/master/tenants`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTenant),
      });
      
      if (res.ok) {
        setShowNewTenant(false);
        setNewTenant({ name: "", email: "", phone: "", plan: "free" });
        fetchTenants();
      }
    } catch (error) {
      console.error("Failed to create tenant:", error);
    } finally {
      setCreating(false);
    }
  };

  const toggleTenantStatus = async (tenantId: string, currentStatus: string) => {
    const endpoint = currentStatus === "active" ? "pause" : "activate";
    try {
      await fetch(`${API_BASE_URL}/api/v1/master/tenants/${tenantId}/${endpoint}`, {
        method: "POST",
      });
      fetchTenants();
    } catch (error) {
      console.error("Failed to toggle tenant status:", error);
    }
  };

  const filteredTenants = tenants.filter(t => 
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.email.toLowerCase().includes(search.toLowerCase()) ||
    t.tenant_id.toLowerCase().includes(search.toLowerCase())
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
      case "trial": return "bg-blue-500/20 text-blue-300 border-blue-500/30";
      case "paused": return "bg-amber-500/20 text-amber-300 border-amber-500/30";
      case "suspended": return "bg-red-500/20 text-red-300 border-red-500/30";
      default: return "bg-zinc-500/20 text-zinc-300 border-zinc-500/30";
    }
  };

  const getPlanColor = (plan: string) => {
    switch (plan) {
      case "enterprise": return "bg-violet-500/20 text-violet-300";
      case "pro": return "bg-cyan-500/20 text-cyan-300";
      default: return "bg-zinc-500/20 text-zinc-300";
    }
  };

  const getHealthColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 50) return "text-amber-400";
    return "text-red-400";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Tenant Management</h2>
          <p className="text-sm text-zinc-400">{tenants.length} total tenants</p>
        </div>
        <button
          onClick={() => setShowNewTenant(true)}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition hover:shadow-violet-500/40"
        >
          <Plus size={18} />
          Add Tenant
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tenants..."
            className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="trial">Trial</option>
          <option value="paused">Paused</option>
          <option value="suspended">Suspended</option>
        </select>

        <select
          value={planFilter}
          onChange={(e) => setPlanFilter(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
        >
          <option value="">All Plans</option>
          <option value="free">Free</option>
          <option value="pro">Pro</option>
          <option value="enterprise">Enterprise</option>
        </select>

        <button
          onClick={fetchTenants}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/10"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Tenants Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="overflow-hidden rounded-2xl border border-white/10 bg-white/5"
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10 bg-black/20">
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">Tenant</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">Plan</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">Health</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-400">Last Active</th>
                <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-zinc-500">
                    Loading tenants...
                  </td>
                </tr>
              ) : filteredTenants.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-zinc-500">
                    No tenants found
                  </td>
                </tr>
              ) : (
                filteredTenants.map((tenant) => (
                  <tr key={tenant.tenant_id} className="transition hover:bg-white/5">
                    <td className="px-4 py-4">
                      <div>
                        <div className="font-medium text-white">{tenant.name}</div>
                        <div className="text-xs text-zinc-500">{tenant.email}</div>
                        <div className="mt-1 font-mono text-[10px] text-zinc-600">{tenant.tenant_id}</div>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${getPlanColor(tenant.plan)}`}>
                        {tenant.plan}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStatusColor(tenant.status)}`}>
                        {tenant.status}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 overflow-hidden rounded-full bg-zinc-800">
                          <div 
                            className={`h-full rounded-full ${
                              tenant.health_score >= 80 ? 'bg-emerald-500' :
                              tenant.health_score >= 50 ? 'bg-amber-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${tenant.health_score}%` }}
                          />
                        </div>
                        <span className={`text-sm font-medium ${getHealthColor(tenant.health_score)}`}>
                          {tenant.health_score}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="text-sm text-zinc-400">
                        {tenant.last_activity 
                          ? new Date(tenant.last_activity).toLocaleDateString()
                          : "Never"
                        }
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <a
                          href={`/master/tenants/${tenant.tenant_id}`}
                          className="rounded-lg p-2 text-zinc-400 transition hover:bg-white/10 hover:text-white"
                          title="View Details"
                        >
                          <Eye size={16} />
                        </a>
                        <button
                          onClick={() => toggleTenantStatus(tenant.tenant_id, tenant.status)}
                          className="rounded-lg p-2 text-zinc-400 transition hover:bg-white/10 hover:text-white"
                          title={tenant.status === "active" ? "Pause" : "Activate"}
                        >
                          {tenant.status === "active" ? <Pause size={16} /> : <Play size={16} />}
                        </button>
                        <a
                          href={`/master/tenants/${tenant.tenant_id}/settings`}
                          className="rounded-lg p-2 text-zinc-400 transition hover:bg-white/10 hover:text-white"
                          title="Settings"
                        >
                          <Settings size={16} />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* New Tenant Modal */}
      {showNewTenant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl"
          >
            <h3 className="text-xl font-bold text-white">Add New Tenant</h3>
            <p className="mt-1 text-sm text-zinc-400">Create a new tenant account</p>

            <div className="mt-6 space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">Business Name</label>
                <input
                  type="text"
                  value={newTenant.name}
                  onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                  placeholder="e.g., Cafe Mellow"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">Email</label>
                <input
                  type="email"
                  value={newTenant.email}
                  onChange={(e) => setNewTenant({ ...newTenant, email: e.target.value })}
                  placeholder="admin@business.com"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">Phone (optional)</label>
                <input
                  type="tel"
                  value={newTenant.phone}
                  onChange={(e) => setNewTenant({ ...newTenant, phone: e.target.value })}
                  placeholder="+91 98765 43210"
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-zinc-500 outline-none focus:border-violet-500/50"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium text-zinc-300">Plan</label>
                <select
                  value={newTenant.plan}
                  onChange={(e) => setNewTenant({ ...newTenant, plan: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-violet-500/50"
                >
                  <option value="free">Free</option>
                  <option value="pro">Pro</option>
                  <option value="enterprise">Enterprise</option>
                </select>
              </div>
            </div>

            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowNewTenant(false)}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-zinc-300 transition hover:bg-white/5"
              >
                Cancel
              </button>
              <button
                onClick={createTenant}
                disabled={creating || !newTenant.name || !newTenant.email}
                className="rounded-xl bg-gradient-to-r from-violet-500 to-purple-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg transition hover:shadow-violet-500/30 disabled:opacity-50"
              >
                {creating ? "Creating..." : "Create Tenant"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
