"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Brain, TrendingUp } from "lucide-react";
import { postJson, API_BASE_URL } from "@/lib/api";
import { useTenant } from "@/contexts/TenantContext";

const API_PREFIX = "/api/v1";

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

export default function SettingsClient({ initial }: { initial: ConfigStatus }) {
  const [cfg, setCfg] = useState<ConfigStatus>(initial);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [projectId, setProjectId] = useState(cfg.PROJECT_ID || "");
  const [datasetId, setDatasetId] = useState(cfg.DATASET_ID || "");
  const [keyFile, setKeyFile] = useState(cfg.KEY_FILE || "service-key.json");

  const [geminiKey, setGeminiKey] = useState("");
  const [ppAppKey, setPpAppKey] = useState("");
  const [ppAppSecret, setPpAppSecret] = useState("");
  const [ppAccessToken, setPpAccessToken] = useState("");
  const [ppMappingCode, setPpMappingCode] = useState("");
  
  const [folderExpenses, setFolderExpenses] = useState("");
  const [folderPurchases, setFolderPurchases] = useState("");
  const [folderInventory, setFolderInventory] = useState("");
  const [folderRecipes, setFolderRecipes] = useState("");
  const [folderWastage, setFolderWastage] = useState("");

  async function refresh() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
    const res = await fetch(`${base}/config`, { cache: "no-store" });
    const data = (await res.json()) as ConfigStatus;
    if (!res.ok) throw new Error("Failed to refresh config");
    setCfg(data);
  }

  async function save() {
    setErr(null);
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
      
      if (folderExpenses.trim()) payload.FOLDER_ID_EXPENSES = folderExpenses.trim();
      if (folderPurchases.trim()) payload.FOLDER_ID_PURCHASES = folderPurchases.trim();
      if (folderInventory.trim()) payload.FOLDER_ID_INVENTORY = folderInventory.trim();
      if (folderRecipes.trim()) payload.FOLDER_ID_RECIPES = folderRecipes.trim();
      if (folderWastage.trim()) payload.FOLDER_ID_WASTAGE = folderWastage.trim();

      // Use PATCH for merge updates - prevents credential overwrites
      const res = await fetch(`${API_BASE_URL}/config`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || `Save failed (${res.status})`);
      }

      const result = await res.json();

      // Clear input fields
      setGeminiKey("");
      setPpAppKey("");
      setPpAppSecret("");
      setPpAccessToken("");
      setPpMappingCode("");
      setFolderExpenses("");
      setFolderPurchases("");
      setFolderInventory("");
      setFolderRecipes("");
      setFolderWastage("");

      // Instant UI update from response
      setCfg({
        ok: true,
        PROJECT_ID: result.PROJECT_ID || "",
        DATASET_ID: result.DATASET_ID || "",
        KEY_FILE: result.KEY_FILE || "service-key.json",
        GEMINI_API_KEY_set: result.GEMINI_API_KEY_set || false,
        PP_APP_KEY_set: result.PP_APP_KEY_set || false,
        PP_APP_SECRET_set: result.PP_APP_SECRET_set || false,
        PP_ACCESS_TOKEN_set: result.PP_ACCESS_TOKEN_set || false,
        PP_MAPPING_CODE_set: result.PP_MAPPING_CODE_set || false,
        FOLDER_ID_EXPENSES_set: result.FOLDER_ID_EXPENSES_set || false,
        FOLDER_ID_PURCHASES_set: result.FOLDER_ID_PURCHASES_set || false,
        FOLDER_ID_INVENTORY_set: result.FOLDER_ID_INVENTORY_set || false,
        FOLDER_ID_RECIPES_set: result.FOLDER_ID_RECIPES_set || false,
        FOLDER_ID_WASTAGE_set: result.FOLDER_ID_WASTAGE_set || false,
      });

      // Show success toast
      alert("✅ Settings saved successfully! System is now live.");
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
        <div className="text-sm font-semibold text-zinc-100">Configuration status</div>
        <div className="mt-2 grid gap-3 md:grid-cols-2">
          <StatusRow label="PROJECT_ID" value={cfg.PROJECT_ID || "—"} />
          <StatusRow label="DATASET_ID" value={cfg.DATASET_ID || "—"} />
          <StatusRow label="KEY_FILE" value={cfg.KEY_FILE || "—"} />
          <StatusBool label="GEMINI_API_KEY" ok={cfg.GEMINI_API_KEY_set} />
          <StatusBool label="PP_APP_KEY" ok={cfg.PP_APP_KEY_set} />
          <StatusBool label="PP_APP_SECRET" ok={cfg.PP_APP_SECRET_set} />
          <StatusBool label="PP_ACCESS_TOKEN" ok={cfg.PP_ACCESS_TOKEN_set} />
          <StatusBool label="PP_MAPPING_CODE" ok={cfg.PP_MAPPING_CODE_set} />
        </div>
        
        <div className="mt-4 text-sm font-semibold text-zinc-100">Google Drive Folders</div>
        <div className="mt-2 grid gap-3 md:grid-cols-3 lg:grid-cols-5">
          <StatusBool label="EXPENSES" ok={cfg.FOLDER_ID_EXPENSES_set} />
          <StatusBool label="PURCHASES" ok={cfg.FOLDER_ID_PURCHASES_set} />
          <StatusBool label="INVENTORY" ok={cfg.FOLDER_ID_INVENTORY_set} />
          <StatusBool label="RECIPES" ok={cfg.FOLDER_ID_RECIPES_set} />
          <StatusBool label="WASTAGE" ok={cfg.FOLDER_ID_WASTAGE_set} />
        </div>
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-4">
        <div className="text-sm font-semibold text-zinc-100">Update secrets & settings</div>
        <div className="mt-1 text-xs text-zinc-500">
          Keys are saved server-side in <span className="font-mono">config_override.json</span>. The UI will never display the secret back.
        </div>

        {err ? (
          <div className="mt-3 rounded-xl border border-red-900/40 bg-red-950/40 px-3 py-2 text-xs text-red-200">
            {err}
          </div>
        ) : null}

        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <Input label="PROJECT_ID" value={projectId} onChange={setProjectId} placeholder="cafe-mellow-core-2026" />
          <Input label="DATASET_ID" value={datasetId} onChange={setDatasetId} placeholder="cafe_operations" />
          <Input label="KEY_FILE" value={keyFile} onChange={setKeyFile} placeholder="service-key.json" />
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <Input label="GEMINI_API_KEY" value={geminiKey} onChange={setGeminiKey} placeholder="Paste new key" secret />
          <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-500">
            Security: rotate any key you posted previously. After saving, restart the API only if needed.
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <Input label="PP_APP_KEY" value={ppAppKey} onChange={setPpAppKey} placeholder="Petpooja key" secret />
          <Input label="PP_APP_SECRET" value={ppAppSecret} onChange={setPpAppSecret} placeholder="Petpooja secret" secret />
          <Input label="PP_ACCESS_TOKEN" value={ppAccessToken} onChange={setPpAccessToken} placeholder="Petpooja token" secret />
          <Input label="PP_MAPPING_CODE" value={ppMappingCode} onChange={setPpMappingCode} placeholder="Restaurant ID" />
        </div>

        <div className="mt-4 text-sm font-semibold text-zinc-100">Google Drive Folder IDs</div>
        <div className="mt-1 text-xs text-zinc-500">
          Paste folder IDs from Google Drive URLs. Share each folder with your service account email.
        </div>
        <div className="mt-2 grid gap-3 md:grid-cols-3 lg:grid-cols-5">
          <Input label="EXPENSES" value={folderExpenses} onChange={setFolderExpenses} placeholder="Folder ID" />
          <Input label="PURCHASES" value={folderPurchases} onChange={setFolderPurchases} placeholder="Folder ID" />
          <Input label="INVENTORY" value={folderInventory} onChange={setFolderInventory} placeholder="Folder ID" />
          <Input label="RECIPES" value={folderRecipes} onChange={setFolderRecipes} placeholder="Folder ID" />
          <Input label="WASTAGE" value={folderWastage} onChange={setFolderWastage} placeholder="Folder ID" />
        </div>

        <div className="mt-4 flex items-center justify-end gap-2">
          <button
            onClick={() => void refresh()}
            className="rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900"
          >
            Refresh
          </button>
          <button
            onClick={() => void save()}
            disabled={saving}
            className="rounded-xl bg-emerald-400 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-sm text-zinc-200">{value}</div>
    </div>
  );
}

function StatusBool({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className={"mt-1 text-sm " + (ok ? "text-emerald-300" : "text-red-300")}>
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
        className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-zinc-600"
      />
    </label>
  );
}
