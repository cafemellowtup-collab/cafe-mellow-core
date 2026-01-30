import SettingsEnhanced from "./SettingsEnhanced";

async function getConfig() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const res = await fetch(`${base}/config`, { 
      cache: "no-store",
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    if (!res.ok) {
      console.error("Config fetch failed:", res.status);
      return getDefaultConfig();
    }
    return res.json();
  } catch (e) {
    console.error("Config fetch error:", e);
    return getDefaultConfig();
  }
}

function getDefaultConfig() {
  return {
    ok: false,
    PROJECT_ID: "",
    DATASET_ID: "",
    KEY_FILE: "service-key.json",
    GEMINI_API_KEY_set: false,
    PP_APP_KEY_set: false,
    PP_APP_SECRET_set: false,
    PP_ACCESS_TOKEN_set: false,
    PP_MAPPING_CODE_set: false,
    FOLDER_ID_EXPENSES_set: false,
    FOLDER_ID_PURCHASES_set: false,
    FOLDER_ID_INVENTORY_set: false,
    FOLDER_ID_RECIPES_set: false,
    FOLDER_ID_WASTAGE_set: false,
  };
}

export default async function SettingsPage() {
  const cfg = await getConfig();
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-100">Ultimate Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Master control: Credentials, AI Learning, System Configuration
        </p>
      </div>
      <SettingsEnhanced initial={cfg} />
    </div>
  );
}
