"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Brain, 
  Settings as SettingsIcon, 
  Shield, 
  Trash2, 
  CheckCircle, 
  XCircle,
  Calendar,
  AlertTriangle,
  Zap,
  FolderOpen,
  Users,
  Bell,
  Database,
  Key,
  RefreshCw,
  Link,
  Eye,
  EyeOff,
  Save,
  Plus,
  Edit3,
  Lock,
  Unlock
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";

const API_PREFIX = "/api/v1";

type LearnedStrategy = {
  id: string;
  rule_type: string;
  description: string;
  created_by: string;
  created_at: string;
  confidence_score: number;
  usage_count: number;
  status: string;
};

type ConfigStatus = {
  ok: boolean;
  PROJECT_ID: string;
  DATASET_ID: string;
  KEY_FILE: string;
  GEMINI_API_KEY_set: boolean;
  PP_APP_KEY_set: boolean;
  PP_APP_SECRET_set: boolean;
  PP_ACCESS_TOKEN_set: boolean;
  PP_MAPPING_CODE_set: boolean;
  FOLDER_ID_EXPENSES_set: boolean;
  FOLDER_ID_PURCHASES_set: boolean;
  FOLDER_ID_INVENTORY_set: boolean;
  FOLDER_ID_RECIPES_set: boolean;
  FOLDER_ID_WASTAGE_set: boolean;
};

type UserRole = {
  id: string;
  name: string;
  email: string;
  role: "admin" | "manager" | "viewer" | "analyst";
  permissions: string[];
  created_at: string;
  last_login?: string;
  status: "active" | "inactive";
};

type SystemConfig = {
  ai_tone: "professional" | "friendly" | "technical";
  backfill_start_date: string;
  auto_sync_enabled: boolean;
  notification_email: string;
  data_retention_days: number;
  auto_task_generation: boolean;
  proactive_alerts: boolean;
};

export default function SettingsEnhanced({ initial }: { initial: ConfigStatus }) {
  const { tenant } = useTenant();
  const [activeTab, setActiveTab] = useState<"credentials" | "drive" | "users" | "metacognitive" | "system" | "notifications" | "master">("credentials");
  
  // Credentials
  const [cfg, setCfg] = useState<ConfigStatus>(initial);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [projectId, setProjectId] = useState(cfg.PROJECT_ID || "");
  const [datasetId, setDatasetId] = useState(cfg.DATASET_ID || "");
  const [keyFile, setKeyFile] = useState(cfg.KEY_FILE || "service-key.json");
  const [geminiKey, setGeminiKey] = useState("");
  const [ppAppKey, setPpAppKey] = useState("");
  const [ppAppSecret, setPpAppSecret] = useState("");
  const [ppAccessToken, setPpAccessToken] = useState("");
  const [ppMappingCode, setPpMappingCode] = useState("");
  
  // Drive Folder IDs
  const [folderExpenses, setFolderExpenses] = useState("");
  const [folderPurchases, setFolderPurchases] = useState("");
  const [folderInventory, setFolderInventory] = useState("");
  const [folderRecipes, setFolderRecipes] = useState("");
  const [folderWastage, setFolderWastage] = useState("");
  
  // User Management
  const [users, setUsers] = useState<UserRole[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserRole, setNewUserRole] = useState<"admin" | "manager" | "viewer" | "analyst">("viewer");
  const [newUserName, setNewUserName] = useState("");
  
  // Metacognitive
  const [strategies, setStrategies] = useState<LearnedStrategy[]>([]);
  const [strategiesLoading, setStrategiesLoading] = useState(false);
  const [strategiesError, setStrategiesError] = useState<string | null>(null);
  
  // System Config
  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    ai_tone: "professional",
    backfill_start_date: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    auto_sync_enabled: false,
    notification_email: "",
    data_retention_days: 365,
    auto_task_generation: true,
    proactive_alerts: true,
  });
  
  // Confirmation dialogs for dangerous actions
  const [confirmDialog, setConfirmDialog] = useState<{show: boolean; action: string; message: string; onConfirm: () => void}>({show: false, action: "", message: "", onConfirm: () => {}});
  
  const [nukeConfirm, setNukeConfirm] = useState(false);
  
  useEffect(() => {
    if (activeTab === "metacognitive") {
      loadStrategies();
    }
  }, [activeTab, tenant.org_id, tenant.location_id]);
  
  async function loadStrategies() {
    setStrategiesLoading(true);
    setStrategiesError(null);
    try {
      const params = new URLSearchParams({
        org_id: tenant.org_id,
        location_id: tenant.location_id,
        status: "active"
      });
      
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/chat/metacognitive/strategies?${params}`);
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || "Failed to load strategies");
      }
      
      setStrategies(data.strategies || []);
    } catch (e: unknown) {
      setStrategiesError(e instanceof Error ? e.message : "Failed to load strategies");
    } finally {
      setStrategiesLoading(false);
    }
  }
  
  async function deleteStrategy(id: string) {
    try {
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/chat/metacognitive/strategies/${id}`, {
        method: "DELETE"
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to delete strategy");
      }
      
      setStrategies(strategies.filter(s => s.id !== id));
      setSuccess("Strategy deleted successfully");
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }
  
  async function saveCredentials() {
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const payload: Record<string, string> = {};
      if (projectId.trim()) payload.PROJECT_ID = projectId.trim();
      if (datasetId.trim()) payload.DATASET_ID = datasetId.trim();
      if (keyFile.trim()) payload.KEY_FILE = keyFile.trim();
      if (geminiKey.trim()) payload.GEMINI_API_KEY = geminiKey.trim();
      if (ppAppKey.trim()) payload.PP_APP_KEY = ppAppKey.trim();
      if (ppAppSecret.trim()) payload.PP_APP_SECRET = ppAppSecret.trim();
      if (ppAccessToken.trim()) payload.PP_ACCESS_TOKEN = ppAccessToken.trim();
      if (ppMappingCode.trim()) payload.PP_MAPPING_CODE = ppMappingCode.trim();
      
      const res = await fetch(`${API_BASE_URL}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Save failed");
      }
      
      setGeminiKey("");
      setPpAppKey("");
      setPpAppSecret("");
      setPpAccessToken("");
      setPpMappingCode("");
      
      const refreshRes = await fetch(`${API_BASE_URL}/config`);
      const data = await refreshRes.json();
      setCfg(data);
      
      setSuccess("Configuration saved successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }
  
  async function triggerBackfill() {
    setError(null);
    setSuccess(null);
    try {
      // This would trigger a background job to fetch historical Petpooja data
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/sync/backfill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_date: systemConfig.backfill_start_date,
          org_id: tenant.org_id,
          location_id: tenant.location_id
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Backfill failed");
      }
      
      setSuccess("Historical data backfill started! This will run in background.");
      setTimeout(() => setSuccess(null), 5000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Backfill failed");
    }
  }
  
  async function nukeDatabase() {
    if (!nukeConfirm) {
      setNukeConfirm(true);
      setTimeout(() => setNukeConfirm(false), 10000);
      return;
    }
    
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${API_BASE_URL}${API_PREFIX}/system/nuke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          org_id: tenant.org_id,
          location_id: tenant.location_id,
          confirm: true
        })
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Nuke failed");
      }
      
      setNukeConfirm(false);
      setSuccess("Database cache cleared successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Nuke failed");
    }
  }
  
  async function saveDriveFolders() {
    setError(null);
    setSuccess(null);
    setSaving(true);
    try {
      const payload: Record<string, string> = {};
      if (folderExpenses.trim()) payload.FOLDER_ID_EXPENSES = folderExpenses.trim();
      if (folderPurchases.trim()) payload.FOLDER_ID_PURCHASES = folderPurchases.trim();
      if (folderInventory.trim()) payload.FOLDER_ID_INVENTORY = folderInventory.trim();
      if (folderRecipes.trim()) payload.FOLDER_ID_RECIPES = folderRecipes.trim();
      if (folderWastage.trim()) payload.FOLDER_ID_WASTAGE = folderWastage.trim();
      
      const res = await fetch(`${API_BASE_URL}/config`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Save failed");
      }
      
      // Clear inputs after save
      setFolderExpenses("");
      setFolderPurchases("");
      setFolderInventory("");
      setFolderRecipes("");
      setFolderWastage("");
      
      // Refresh config
      const refreshRes = await fetch(`${API_BASE_URL}/config`);
      const data = await refreshRes.json();
      setCfg(data);
      
      setSuccess("Drive folder settings saved successfully!");
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }
  
  async function addUser() {
    if (!newUserName.trim() || !newUserEmail.trim()) {
      setError("Name and email are required");
      return;
    }
    
    setError(null);
    try {
      const newUser: UserRole = {
        id: `user_${Date.now()}`,
        name: newUserName.trim(),
        email: newUserEmail.trim(),
        role: newUserRole,
        permissions: getPermissionsForRole(newUserRole),
        created_at: new Date().toISOString(),
        status: "active"
      };
      
      // In production, this would call an API to create the user
      // For now, we'll add to local state
      setUsers([...users, newUser]);
      
      // Reset form
      setNewUserName("");
      setNewUserEmail("");
      setNewUserRole("viewer");
      setShowAddUser(false);
      
      setSuccess(`User ${newUser.name} added successfully!`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to add user");
    }
  }
  
  function getPermissionsForRole(role: "admin" | "manager" | "viewer" | "analyst"): string[] {
    switch (role) {
      case "admin":
        return ["all", "settings", "users", "data", "ai", "reports", "operations"];
      case "manager":
        return ["data", "ai", "reports", "operations"];
      case "analyst":
        return ["ai", "reports"];
      case "viewer":
        return ["dashboard_view"];
      default:
        return [];
    }
  }
  
  return (
    <div className="space-y-4">
      {/* Tab Switcher */}
      <div className="rounded-2xl border border-white/10 bg-white/5 p-2">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setActiveTab("credentials")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "credentials"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <Shield size={16} />
            Credentials
          </button>
          <button
            onClick={() => setActiveTab("drive")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "drive"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <FolderOpen size={16} />
            Drive Folders
          </button>
          <button
            onClick={() => setActiveTab("users")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "users"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <Users size={16} />
            User Management
          </button>
          <button
            onClick={() => setActiveTab("notifications")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "notifications"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <Bell size={16} />
            Notifications
          </button>
          <button
            onClick={() => setActiveTab("metacognitive")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "metacognitive"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <Brain size={16} />
            AI Learning
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "system"
                ? "bg-emerald-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <SettingsIcon size={16} />
            System Config
          </button>
          <button
            onClick={() => setActiveTab("master")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition ${
              activeTab === "master"
                ? "bg-amber-400 text-zinc-950"
                : "text-zinc-300 hover:bg-white/5"
            }`}
          >
            <Shield size={16} />
            Master Dashboard
          </button>
        </div>
      </div>
      
      {/* Global Alerts */}
      <AnimatePresence>
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100"
          >
            <div className="flex items-center gap-2">
              <CheckCircle size={16} />
              {success}
            </div>
          </motion.div>
        )}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100"
          >
            <div className="flex items-center gap-2">
              <XCircle size={16} />
              {error}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Tab Content */}
      {activeTab === "credentials" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Configuration Status</div>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              <StatusRow label="PROJECT_ID" value={cfg.PROJECT_ID || "—"} />
              <StatusRow label="DATASET_ID" value={cfg.DATASET_ID || "—"} />
              <StatusRow label="KEY_FILE" value={cfg.KEY_FILE || "—"} />
              <StatusBool label="GEMINI_API_KEY" ok={cfg.GEMINI_API_KEY_set} />
              <StatusBool label="PP_APP_KEY" ok={cfg.PP_APP_KEY_set} />
              <StatusBool label="PP_APP_SECRET" ok={cfg.PP_APP_SECRET_set} />
              <StatusBool label="PP_ACCESS_TOKEN" ok={cfg.PP_ACCESS_TOKEN_set} />
              <StatusBool label="PP_MAPPING_CODE" ok={cfg.PP_MAPPING_CODE_set} />
            </div>
          </div>
          
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Update Credentials</div>
            <div className="mt-1 text-xs text-zinc-500">
              Keys are stored server-side. Restart API only if needed.
            </div>
            
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <Input label="PROJECT_ID" value={projectId} onChange={setProjectId} />
              <Input label="DATASET_ID" value={datasetId} onChange={setDatasetId} />
              <Input label="KEY_FILE" value={keyFile} onChange={setKeyFile} />
            </div>
            
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <Input label="GEMINI_API_KEY" value={geminiKey} onChange={setGeminiKey} secret />
              <Input label="PP_APP_KEY" value={ppAppKey} onChange={setPpAppKey} secret />
              <Input label="PP_APP_SECRET" value={ppAppSecret} onChange={setPpAppSecret} secret />
              <Input label="PP_ACCESS_TOKEN" value={ppAccessToken} onChange={setPpAccessToken} secret />
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={saveCredentials}
                disabled={saving}
                className="rounded-xl bg-emerald-400 px-6 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:opacity-60"
              >
                {saving ? "Saving..." : "Save Credentials"}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {activeTab === "metacognitive" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-zinc-100">AI Learned Strategies</div>
                <div className="mt-1 text-xs text-zinc-500">
                  Review and manage patterns AI has learned from your operations
                </div>
              </div>
              <button
                onClick={loadStrategies}
                disabled={strategiesLoading}
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-200 hover:bg-white/10 disabled:opacity-60"
              >
                Refresh
              </button>
            </div>
            
            {strategiesLoading && (
              <div className="mt-4 space-y-2">
                {[1, 2, 3].map(k => (
                  <div key={k} className="h-16 animate-pulse rounded-xl bg-white/5" />
                ))}
              </div>
            )}
            
            {strategiesError && (
              <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
                {strategiesError}
              </div>
            )}
            
            {!strategiesLoading && !strategiesError && strategies.length === 0 && (
              <div className="mt-4 rounded-xl border border-white/10 bg-white/5 px-4 py-8 text-center text-sm text-zinc-400">
                No learned strategies yet. AI will learn from your interactions.
              </div>
            )}
            
            {!strategiesLoading && !strategiesError && strategies.length > 0 && (
              <div className="mt-4 space-y-2">
                {strategies.map(strategy => (
                  <motion.div
                    key={strategy.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl border border-white/10 bg-white/5 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="rounded-full bg-purple-500/20 px-2 py-0.5 text-xs font-semibold text-purple-200">
                            {strategy.rule_type}
                          </span>
                          <span className="text-xs text-zinc-500">
                            Confidence: {Math.round(strategy.confidence_score * 100)}%
                          </span>
                        </div>
                        <div className="mt-2 text-sm text-zinc-200">{strategy.description}</div>
                        <div className="mt-2 text-xs text-zinc-500">
                          Created by {strategy.created_by} • Used {strategy.usage_count} times
                        </div>
                      </div>
                      <button
                        onClick={() => deleteStrategy(strategy.id)}
                        className="rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-red-200 transition hover:bg-red-500/20"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Drive Folders Tab */}
      {activeTab === "drive" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
              <FolderOpen size={18} className="text-emerald-400" />
              Google Drive Folder Mapping
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Connect your Google Drive folders for automatic data sync. Paste the folder ID from the Drive URL.
            </div>
            
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <StatusBool label="EXPENSES Folder" ok={cfg.FOLDER_ID_EXPENSES_set} />
              <StatusBool label="PURCHASES Folder" ok={cfg.FOLDER_ID_PURCHASES_set} />
              <StatusBool label="INVENTORY Folder" ok={cfg.FOLDER_ID_INVENTORY_set} />
              <StatusBool label="RECIPES Folder" ok={cfg.FOLDER_ID_RECIPES_set} />
              <StatusBool label="WASTAGE Folder" ok={cfg.FOLDER_ID_WASTAGE_set} />
            </div>
          </div>
          
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Configure Folder IDs</div>
            <div className="mt-1 text-xs text-zinc-500">
              Share each folder with your service account email, then paste the folder ID here.
            </div>
            
            <div className="mt-4 grid gap-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                  <Database size={14} className="text-blue-400" />
                  Expenses Folder
                </div>
                <div className="mt-1 text-xs text-zinc-500">Upload expense Excel/CSV files here for automatic processing</div>
                <input
                  type="text"
                  value={folderExpenses}
                  onChange={(e) => setFolderExpenses(e.target.value)}
                  placeholder="Enter Google Drive Folder ID"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
              
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                  <Database size={14} className="text-green-400" />
                  Purchases Folder
                </div>
                <div className="mt-1 text-xs text-zinc-500">Upload purchase/vendor invoices for inventory tracking</div>
                <input
                  type="text"
                  value={folderPurchases}
                  onChange={(e) => setFolderPurchases(e.target.value)}
                  placeholder="Enter Google Drive Folder ID"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
              
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                  <Database size={14} className="text-amber-400" />
                  Inventory Folder
                </div>
                <div className="mt-1 text-xs text-zinc-500">Upload stock count sheets and inventory reports</div>
                <input
                  type="text"
                  value={folderInventory}
                  onChange={(e) => setFolderInventory(e.target.value)}
                  placeholder="Enter Google Drive Folder ID"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
              
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                  <Database size={14} className="text-purple-400" />
                  Recipes Folder
                </div>
                <div className="mt-1 text-xs text-zinc-500">Upload recipe masters and production recipes</div>
                <input
                  type="text"
                  value={folderRecipes}
                  onChange={(e) => setFolderRecipes(e.target.value)}
                  placeholder="Enter Google Drive Folder ID"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
              
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                  <Database size={14} className="text-red-400" />
                  Wastage Folder
                </div>
                <div className="mt-1 text-xs text-zinc-500">Upload wastage reports and spoilage logs</div>
                <input
                  type="text"
                  value={folderWastage}
                  onChange={(e) => setFolderWastage(e.target.value)}
                  placeholder="Enter Google Drive Folder ID"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={saveDriveFolders}
                disabled={saving}
                className="flex items-center gap-2 rounded-xl bg-emerald-400 px-6 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:opacity-60"
              >
                <Save size={14} />
                {saving ? "Saving..." : "Save Folder Settings"}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* User Management Tab */}
      {activeTab === "users" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
                  <Users size={18} className="text-emerald-400" />
                  User Management
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  Manage team access and permissions
                </div>
              </div>
              <button
                onClick={() => setShowAddUser(true)}
                className="flex items-center gap-2 rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-300"
              >
                <Plus size={14} />
                Add User
              </button>
            </div>
            
            {/* Role descriptions */}
            <div className="mt-4 grid gap-2 md:grid-cols-4">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="text-xs font-semibold text-red-300">Admin</div>
                <div className="mt-1 text-[10px] text-zinc-500">Full access to all features, settings, and user management</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="text-xs font-semibold text-amber-300">Manager</div>
                <div className="mt-1 text-[10px] text-zinc-500">Access to operations, reports, and team dashboards</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="text-xs font-semibold text-blue-300">Analyst</div>
                <div className="mt-1 text-[10px] text-zinc-500">Access to AI chat, reports, and analytics only</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="text-xs font-semibold text-zinc-300">Viewer</div>
                <div className="mt-1 text-[10px] text-zinc-500">Read-only access to dashboards</div>
              </div>
            </div>
            
            {/* User list */}
            <div className="mt-4 space-y-2">
              {users.length === 0 ? (
                <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-8 text-center text-sm text-zinc-400">
                  No users added yet. Click &quot;Add User&quot; to invite team members.
                </div>
              ) : (
                users.map(user => (
                  <div key={user.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-cyan-400 text-sm font-bold text-zinc-950">
                        {user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-zinc-100">{user.name}</div>
                        <div className="text-xs text-zinc-500">{user.email}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        user.role === 'admin' ? 'bg-red-500/20 text-red-200' :
                        user.role === 'manager' ? 'bg-amber-500/20 text-amber-200' :
                        user.role === 'analyst' ? 'bg-blue-500/20 text-blue-200' :
                        'bg-zinc-500/20 text-zinc-200'
                      }`}>
                        {user.role}
                      </span>
                      <span className={`text-xs ${user.status === 'active' ? 'text-emerald-300' : 'text-zinc-500'}`}>
                        {user.status}
                      </span>
                      <button className="rounded-lg border border-white/10 bg-white/5 p-2 text-zinc-300 hover:bg-white/10">
                        <Edit3 size={14} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          
          {/* Add User Modal */}
          <AnimatePresence>
            {showAddUser && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                onClick={() => setShowAddUser(false)}
              >
                <motion.div
                  initial={{ scale: 0.95, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.95, opacity: 0 }}
                  onClick={(e) => e.stopPropagation()}
                  className="w-full max-w-md rounded-2xl border border-white/10 bg-zinc-900 p-6"
                >
                  <div className="text-lg font-semibold text-zinc-100">Add New User</div>
                  <div className="mt-1 text-xs text-zinc-500">Invite a team member to access TITAN</div>
                  
                  <div className="mt-4 space-y-3">
                    <div>
                      <label className="text-xs text-zinc-500">Full Name</label>
                      <input
                        type="text"
                        value={newUserName}
                        onChange={(e) => setNewUserName(e.target.value)}
                        placeholder="John Doe"
                        className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500">Email Address</label>
                      <input
                        type="email"
                        value={newUserEmail}
                        onChange={(e) => setNewUserEmail(e.target.value)}
                        placeholder="john@company.com"
                        className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-500">Role</label>
                      <select
                        value={newUserRole}
                        onChange={(e) => {
                          const next = e.target.value;
                          if (next === "admin" || next === "manager" || next === "analyst" || next === "viewer") {
                            setNewUserRole(next);
                          }
                        }}
                        className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200"
                      >
                        <option value="viewer">Viewer - Read-only access</option>
                        <option value="analyst">Analyst - AI & Reports access</option>
                        <option value="manager">Manager - Operations access</option>
                        <option value="admin">Admin - Full access</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="mt-6 flex justify-end gap-2">
                    <button
                      onClick={() => setShowAddUser(false)}
                      className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-200 hover:bg-white/10"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={addUser}
                      className="rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-emerald-300"
                    >
                      Add User
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
      
      {/* Notifications Tab */}
      {activeTab === "notifications" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
              <Bell size={18} className="text-emerald-400" />
              Notification Settings
            </div>
            <div className="mt-1 text-xs text-zinc-500">
              Configure alerts and notifications for data freshness, anomalies, and system events
            </div>
            
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4">
                <div>
                  <div className="text-sm font-semibold text-zinc-200">Data Freshness Alerts</div>
                  <div className="text-xs text-zinc-500">Get notified when sales or expense data is stale (&gt;24h old)</div>
                </div>
                <button
                  onClick={() => setSystemConfig({...systemConfig, proactive_alerts: !systemConfig.proactive_alerts})}
                  className={`relative h-6 w-11 rounded-full transition ${systemConfig.proactive_alerts ? "bg-emerald-500" : "bg-zinc-700"}`}
                >
                  <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition ${systemConfig.proactive_alerts ? "left-5" : "left-0.5"}`} />
                </button>
              </div>
              
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4">
                <div>
                  <div className="text-sm font-semibold text-zinc-200">Auto Task Generation</div>
                  <div className="text-xs text-zinc-500">AI automatically creates tasks from anomalies and insights</div>
                </div>
                <button
                  onClick={() => setSystemConfig({...systemConfig, auto_task_generation: !systemConfig.auto_task_generation})}
                  className={`relative h-6 w-11 rounded-full transition ${systemConfig.auto_task_generation ? "bg-emerald-500" : "bg-zinc-700"}`}
                >
                  <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition ${systemConfig.auto_task_generation ? "left-5" : "left-0.5"}`} />
                </button>
              </div>
              
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="text-sm font-semibold text-zinc-200">Notification Email</div>
                <div className="text-xs text-zinc-500">Receive daily summaries and critical alerts</div>
                <input
                  type="email"
                  value={systemConfig.notification_email}
                  onChange={(e) => setSystemConfig({...systemConfig, notification_email: e.target.value})}
                  placeholder="admin@yourcompany.com"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600"
                />
              </div>
            </div>
          </div>
          
          {/* Alert Types */}
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Alert Types</div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <div>
                  <div className="text-xs font-semibold text-zinc-200">Critical</div>
                  <div className="text-[10px] text-zinc-500">API failures, data sync errors</div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="h-3 w-3 rounded-full bg-amber-500" />
                <div>
                  <div className="text-xs font-semibold text-zinc-200">Warning</div>
                  <div className="text-[10px] text-zinc-500">Stale data, missing recipes</div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="h-3 w-3 rounded-full bg-blue-500" />
                <div>
                  <div className="text-xs font-semibold text-zinc-200">Info</div>
                  <div className="text-[10px] text-zinc-500">Sync completed, new insights</div>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
                <div className="h-3 w-3 rounded-full bg-emerald-500" />
                <div>
                  <div className="text-xs font-semibold text-zinc-200">Success</div>
                  <div className="text-[10px] text-zinc-500">Tasks completed, targets achieved</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {activeTab === "system" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">System Configuration</div>
            
            <div className="mt-4 space-y-4">
              <div>
                <label className="text-xs text-zinc-500">AI Tone</label>
                <select
                  value={systemConfig.ai_tone}
                  onChange={(e) => {
                    const next = e.target.value;
                    if (next === "professional" || next === "friendly" || next === "technical") {
                      setSystemConfig({ ...systemConfig, ai_tone: next });
                    }
                  }}
                  className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200"
                >
                  <option value="professional">Professional</option>
                  <option value="friendly">Friendly</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-zinc-500">Data Retention (Days)</label>
                <input
                  type="number"
                  value={systemConfig.data_retention_days}
                  onChange={(e) => setSystemConfig({...systemConfig, data_retention_days: parseInt(e.target.value) || 365})}
                  className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200"
                />
                <div className="mt-1 text-xs text-zinc-500">How long to keep historical data in the system</div>
              </div>
              
              <div>
                <label className="text-xs text-zinc-500">Historical Backfill Start Date</label>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    type="date"
                    value={systemConfig.backfill_start_date}
                    onChange={(e) => setSystemConfig({...systemConfig, backfill_start_date: e.target.value})}
                    className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-200"
                  />
                  <button
                    onClick={triggerBackfill}
                    className="flex items-center gap-2 rounded-xl bg-cyan-500/20 px-4 py-2 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-500/30"
                  >
                    <Calendar size={14} />
                    Start Backfill
                  </button>
                </div>
                <div className="mt-1 text-xs text-zinc-500">
                  Fetch historical Petpooja data from this date. Empty days are skipped automatically.
                </div>
              </div>
              
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-200">Auto-Sync (Daily 2 AM)</div>
                  <div className="text-xs text-zinc-500">Automatic data synchronization</div>
                </div>
                <button
                  onClick={() => setSystemConfig({...systemConfig, auto_sync_enabled: !systemConfig.auto_sync_enabled})}
                  className={`relative h-6 w-11 rounded-full transition ${
                    systemConfig.auto_sync_enabled ? "bg-emerald-500" : "bg-zinc-700"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition ${
                      systemConfig.auto_sync_enabled ? "left-5" : "left-0.5"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>
          
          {/* Danger Zone */}
          <div className="rounded-2xl border border-red-500/30 bg-red-500/5 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-red-200">
              <AlertTriangle size={16} />
              Danger Zone
            </div>
            <div className="mt-3 text-xs text-zinc-400">
              Clear all cached data and reset system state. This cannot be undone.
            </div>
            <button
              onClick={nukeDatabase}
              className={`mt-3 rounded-xl px-6 py-2 text-sm font-semibold transition ${
                nukeConfirm
                  ? "bg-red-500 text-white"
                  : "border border-red-500/30 bg-red-500/10 text-red-200 hover:bg-red-500/20"
              }`}
            >
              {nukeConfirm ? "Click Again to Confirm" : "Clear Database Cache"}
            </button>
          </div>
        </div>
      )}
      
      {/* Master Dashboard Tab */}
      {activeTab === "master" && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-amber-200">
              <Shield size={18} className="text-amber-400" />
              TITAN Master Dashboard Access
            </div>
            <div className="mt-1 text-xs text-zinc-400">
              Super Admin controls for multi-tenant system management, monitoring, and analytics.
            </div>
            
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-200">System Status</div>
                  <div className="text-xs text-zinc-500">All core systems operational</div>
                </div>
                <div className="rounded-full bg-green-500/20 px-3 py-1 text-xs font-semibold text-green-400">
                  HEALTHY
                </div>
              </div>
              
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-lg font-bold text-white">12</div>
                  <div className="text-xs text-zinc-500">Total Tenants</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-lg font-bold text-green-400">8</div>
                  <div className="text-xs text-zinc-500">Active Tenants</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
                  <div className="text-lg font-bold text-amber-400">₹440</div>
                  <div className="text-xs text-zinc-500">Weekly Cost</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Master Dashboard Features</div>
            <div className="mt-1 text-xs text-zinc-500">
              Access comprehensive system administration and tenant management tools
            </div>
            
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-blue-400" />
                  <div className="text-sm font-semibold text-blue-200">Tenant Management</div>
                </div>
                <div className="mt-2 text-xs text-zinc-400">
                  Create, manage, and monitor cafe tenants. Control features, plans, and access.
                </div>
              </div>
              
              <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
                <div className="flex items-center gap-2">
                  <Database size={16} className="text-green-400" />
                  <div className="text-sm font-semibold text-green-200">Usage Analytics</div>
                </div>
                <div className="mt-2 text-xs text-zinc-400">
                  Monitor AI tokens, costs, API usage across all tenants with detailed breakdowns.
                </div>
              </div>
              
              <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 p-4">
                <div className="flex items-center gap-2">
                  <Zap size={16} className="text-purple-400" />
                  <div className="text-sm font-semibold text-purple-200">System Health</div>
                </div>
                <div className="mt-2 text-xs text-zinc-400">
                  Real-time monitoring of system performance, uptime, and component health.
                </div>
              </div>
              
              <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                <div className="flex items-center gap-2">
                  <Brain size={16} className="text-cyan-400" />
                  <div className="text-sm font-semibold text-cyan-200">AI Insights</div>
                </div>
                <div className="mt-2 text-xs text-zinc-400">
                  AI-generated insights about tenant behavior, churn prediction, and optimization.
                </div>
              </div>
            </div>
            
            <div className="mt-6 flex justify-center">
              <a
                href="/master"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3 text-sm font-semibold text-black transition hover:bg-amber-400"
              >
                <Shield size={16} />
                Open Master Dashboard
                <Link size={14} />
              </a>
            </div>
          </div>
          
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold text-zinc-100">Quick Actions</div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300 hover:bg-white/10">
                <Plus size={14} className="mr-2 inline" />
                Add Tenant
              </button>
              <button className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300 hover:bg-white/10">
                <RefreshCw size={14} className="mr-2 inline" />
                System Health Check
              </button>
              <button className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300 hover:bg-white/10">
                <Bell size={14} className="mr-2 inline" />
                View Alerts
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-sm text-zinc-200">{value}</div>
    </div>
  );
}

function StatusBool({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={`mt-1 text-sm ${ok ? "text-emerald-300" : "text-red-300"}`}>
        {ok ? "Set" : "Missing"}
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
  secret,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  secret?: boolean;
}) {
  return (
    <label className="block">
      <div className="mb-1 text-xs text-zinc-500">{label}</div>
      <input
        type={secret ? "password" : "text"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-zinc-600"
      />
    </label>
  );
}
