"""
TITAN Command Center — Self-Developing, Petpooja-Rivaling Intelligence ERP
Modular Pillar Architecture: business logic in pillars/; UI is a window to the logic.
"""
import json
import os
import subprocess
import sys
import threading
import warnings
from datetime import datetime

# Suppress BigQuery "Storage module not found" UserWarning when pyarrow/bq-storage aren't installed.
# The client falls back to REST; we add google-cloud-bigquery-storage[pyarrow] in requirements to avoid it.
warnings.filterwarnings("ignore", message="BigQuery Storage module not found", category=UserWarning)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
from googleapiclient.discovery import build
import settings
from utils.bq_guardrails import query_to_df

# Project root for paths (robust to cwd)
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Pillar imports ---
from pillars.evolution import ensure_dev_evolution_table, get_evolution_suggestions, update_development_status
from pillars.dashboard import get_revenue_expenses_data, get_sentinel_health, get_ai_observations, get_sync_freshness
from pillars.config_vault import EffectiveSettings, save_config_override
from pillars.system_logger import ensure_system_sync_log_table
from pillars.users_roles import get_roles, get_tab_access, get_users, set_user, delete_user, update_user, get_user_by_username, add_user as user_add, TAB_KEYS
from pillars.chat_intel import maybe_log_logic_gap
from pillars.system_logger import log_error, ensure_system_error_log_table

# --- Global excepthook: log any uncaught exception to logs/titan_system_log.txt ---
_orig_excepthook = sys.excepthook
def _titan_excepthook(typ, val, tb):
    try:
        fn = tb.tb_frame.f_code.co_filename if tb else ""
        ln = tb.tb_lineno if tb else None
        log_error("titan_app", str(val), exc_info=(typ, val, tb), file_path=fn, line_number=ln)
    except Exception:
        pass
    _orig_excepthook(typ, val, tb)
sys.excepthook = _titan_excepthook

# --- Page config ---
st.set_page_config(
    page_title="TITAN COMMAND CENTER",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- Glassmorphism Dark Mode CSS ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    /* Base dark theme */
    .stApp { background: linear-gradient(160deg, #0b0f14 0%, #111820 40%, #0d1117 100%); }
    .main .block-container { padding: 2rem 3rem; max-width: 1600px; }
    
    /* Glassmorphism panels */
    .glass-panel {
        background: rgba(22, 27, 34, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.25rem 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .glass-panel strong { color: #e6edf3; font-family: 'Outfit', sans-serif; }
    
    /* Typography */
    h1, h2, h3 { font-family: 'Outfit', sans-serif !important; font-weight: 600; color: #e6edf3 !important; }
    h1 { font-size: 2rem; letter-spacing: -0.02em; background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    p, span, label { color: #8b949e !important; font-family: 'Outfit', sans-serif; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0d1117 0%, #161b22 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: #c9d1d9; }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: rgba(22,27,34,0.5); border-radius: 12px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { background: transparent; color: #8b949e; font-family: 'Outfit', sans-serif; font-weight: 500; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: rgba(139,92,246,0.2); color: #a78bfa; }
    
    /* Metric cards */
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; color: #e6edf3 !important; }
    [data-testid="stMetricDelta"] { font-family: 'Outfit', sans-serif; }
    
    /* Buttons */
    .stButton > button { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important; color: #fff !important; border: none !important; border-radius: 10px !important; font-family: 'Outfit', sans-serif !important; font-weight: 500 !important; transition: all 0.2s !important; }
    .stButton > button:hover { box-shadow: 0 0 24px rgba(139,92,246,0.4); transform: translateY(-1px); }
    
    /* AI Observation chips */
    .obs-chip { display: inline-block; padding: 0.35rem 0.75rem; border-radius: 20px; font-size: 0.8rem; margin: 0.25rem; font-family: 'Outfit', sans-serif; }
    .obs-high { background: rgba(239,68,68,0.2); border: 1px solid rgba(239,68,68,0.4); color: #fca5a5; }
    .obs-medium { background: rgba(245,158,11,0.2); border: 1px solid rgba(245,158,11,0.4); color: #fcd34d; }
    .obs-low { background: rgba(34,197,94,0.2); border: 1px solid rgba(34,197,94,0.4); color: #86efac; }
    
    /* Plotly container */
    .js-plotly-plot { border-radius: 12px; overflow: hidden; }
    
    /* Reduce full-app loading overlay: avoid dimming whole app on button/spinner */
    [data-testid="stAppViewContainer"] { opacity: 1 !important; }
    .stApp { opacity: 1 !important; }
    
    /* Intelligence Chat: assistant replies — clear fonts, full opacity */
    [data-testid="stChatMessage"] .stMarkdown, [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        color: #e6edf3 !important; opacity: 1 !important; font-size: 0.95rem !important;
        font-family: 'Outfit', sans-serif !important; line-height: 1.5 !important;
    }
    [data-testid="stChatMessage"] .stMarkdown strong { color: #f0f6fc !important; }
</style>
""", unsafe_allow_html=True)

# --- BigQuery client (graceful degradation if KEY_FILE missing or BQ unreachable) ---
@st.cache_resource(show_spinner=False)
def _get_bq_client(_key_path: str):
    return bigquery.Client.from_service_account_json(_key_path)

client = None
_key_file = getattr(settings, "KEY_FILE", "service-key.json")
_key_path = _key_file if os.path.isabs(_key_file) else os.path.join(_PROJECT_ROOT, _key_file)
try:
    if not os.path.exists(_key_path):
        raise FileNotFoundError(f"Key file not found: {_key_path}")
    client = _get_bq_client(_key_path)
    client.get_dataset(f"{settings.PROJECT_ID}.{settings.DATASET_ID}")
except FileNotFoundError as e:
    log_error("titan_app", str(e), file_path=__file__, line_number=96)
    client = None
except NotFound as e:
    log_error("titan_app", str(e), file_path=__file__, line_number=99)
    client = None
except Exception as e:
    log_error("titan_app", str(e), exc_info=sys.exc_info(), file_path=__file__, line_number=102)
    client = None

if client is None:
    st.warning("⚠️ BigQuery is not connected. Configure `service-key.json` and a valid dataset. Dashboard, Chat, and Evolution Lab need BQ.")

# --- Cached data helper functions ---
@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_anomaly(days: int):
    return get_anomaly_status(client, settings, days=days)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_freshness():
    return get_sync_freshness(client, settings)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_obs(limit: int):
    return get_ai_observations(client, settings, limit=limit)

@st.cache_data(ttl=300, show_spinner=False)
def _cached_get_rev_exp(days: int):
    return get_revenue_expenses_data(client, settings, days=days)

@st.cache_data(ttl=120, show_spinner=False)
def _cached_get_tasks(limit: int):
    return get_sentinel_health(client, settings, limit=limit)

# --- Self-Storage: ensure dev_evolution_log, system_error_log, system_sync_log exist (only when BQ connected) ---
if client:
    try:
        _e, _c = ensure_dev_evolution_table(client, settings)
        if _c and "evolution_created" not in st.session_state:
            st.session_state.evolution_created = True
        ensure_system_error_log_table(client, settings)
        ensure_system_sync_log_table(client, settings)
        try:
            client.query(f"ALTER TABLE `{settings.PROJECT_ID}.{settings.DATASET_ID}.{getattr(settings,'TABLE_SYSTEM_SYNC_LOG','system_sync_log')}` ADD COLUMN triggered_by STRING")
        except Exception:
            pass
    except Exception as e:
        log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__, line_number=113)
        st.warning(f"Evolution/Log table check failed: {e}. Evolution Lab and BQ error log may not work.")

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1.25rem; background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3); border-radius: 12px; margin-bottom: 1rem;">
        <h2 style="color: #e6edf3; margin: 0; font-family: 'Outfit', sans-serif;">🧬 TITAN ERP</h2>
        <p style="color: #8b949e; margin: 0.4rem 0 0 0; font-size: 0.9rem;">Cafe Mellow Command Center</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### System")
    _dna_path = os.path.join(_PROJECT_ROOT, "TITAN_DNA.json")
    if os.path.exists(_dna_path):
        with open(_dna_path, "r", encoding="utf-8") as f:
            st.json(json.load(f), expanded=False)
    else:
        st.caption("Run titan_dna to see blueprint.")
    st.markdown("---")
    st.markdown("### Quick Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Update DNA", use_container_width=True, key="btn_dna"):
            with st.spinner("Updating..."):
                _dna_script = os.path.join(_PROJECT_ROOT, "04_Intelligence_Lab", "titan_dna.py")
                r = subprocess.run([sys.executable, _dna_script], capture_output=True, text=True, encoding="utf-8", cwd=_PROJECT_ROOT, timeout=30)
                st.success("DNA updated.") if r.returncode == 0 else st.error("DNA failed")
                if r.returncode == 0: st.rerun()
    with c2:
        if st.button("Run Sentinel", use_container_width=True, key="btn_sentinel"):
            with st.spinner("Scanning..."):
                _sentinel_script = os.path.join(_PROJECT_ROOT, "04_Intelligence_Lab", "sentinel_hub.py")
                r = subprocess.run([sys.executable, _sentinel_script], capture_output=True, text=True, encoding="utf-8", cwd=_PROJECT_ROOT, timeout=300)
                st.success("Sentinel done.") if r.returncode == 0 else st.error("Sentinel failed")
                if r.returncode == 0: st.rerun()
    st.markdown("---")
    st.markdown("### Drive Connectivity")
    _drive_ok = 0
    _drive_total = 0
    _drive_service = None
    if os.path.exists(_key_path):
        try:
            _creds = service_account.Credentials.from_service_account_file(_key_path, scopes=settings.SCOPE_URL)
            _drive_service = build("drive", "v3", credentials=_creds)
        except Exception:
            _drive_service = None
    _folders = [
        ("Expenses", getattr(settings, "FOLDER_ID_EXPENSES", "")),
        ("Cash Ops", getattr(settings, "FOLDER_ID_CASH_OPS", "")),
        ("Recipes", getattr(settings, "FOLDER_ID_RECIPES", "")),
        ("Purchases", getattr(settings, "FOLDER_ID_PURCHASES", "")),
        ("Wastage", getattr(settings, "FOLDER_ID_WASTAGE", "")),
    ]
    for _label, _fid in _folders:
        if not _fid:
            st.caption(f"❌ {_label}: No Folder ID in settings")
            _drive_total += 1
            continue
        _drive_total += 1
        _ok = False
        if _drive_service:
            try:
                _drive_service.files().list(q=f"'{_fid}' in parents and trashed=false", pageSize=1, fields="files(id)").execute()
                _ok = True
                _drive_ok += 1
            except Exception:
                pass
        if _ok:
            st.caption(f"✅ {_label}")
        else:
            st.caption(f"❌ {_label}")
    if _drive_total > 0 and _drive_ok < _drive_total:
        st.error("Fix Permissions: Share each Drive folder with the service account email (Viewer). Check service-key.json and folder IDs in settings.")
    with st.expander("🔐 Configuration Status", expanded=False):
        st.caption(f"BigQuery: {'Connected' if client else 'Not connected'}")
        _gk = getattr(settings, "GEMINI_API_KEY", "")
        st.caption(f"Gemini API Key: {'Set' if bool(_gk) else 'Missing'}")
        _ppk = getattr(settings, "PP_APP_KEY", "")
        _pps = getattr(settings, "PP_APP_SECRET", "")
        _ppt = getattr(settings, "PP_ACCESS_TOKEN", "")
        _ppm = getattr(settings, "PP_MAPPING_CODE", "")
        _pp_ok = bool(_ppk and _pps and _ppt and _ppm)
        st.caption(f"Petpooja API: {'Configured' if _pp_ok else 'Missing fields'}")
        for _n, _v in [("PP_APP_KEY", _ppk), ("PP_APP_SECRET", _pps), ("PP_ACCESS_TOKEN", _ppt), ("PP_MAPPING_CODE", _ppm)]:
            st.caption(f"  - {_n}: {'Set' if bool(_v) else 'Missing'}")
    st.markdown("---")
    st.caption("Log: logs/titan_system_log.txt")
    _role = st.selectbox("Role (for access)", ["Admin", "Manager", "Staff"], index=0, key="sidebar_role")
    if "_titan_role" not in st.session_state:
        st.session_state._titan_role = "Admin"
    st.session_state._titan_role = _role
    st.caption("Status: Operational")

# --- Role and tab visibility ---
def _can(tab_key): return tab_key in get_tab_access(st.session_state.get("_titan_role", "Admin"))

# --- Five main tabs ---
tab_dash, tab_chat, tab_users, tab_config, tab_evo = st.tabs([
    "💎 Executive Dashboard",
    "🧠 Intelligence Chat",
    "👥 User & Rights",
    "⚙️ API & Config Center",
    "🧪 Evolution Lab",
])

# ========== 1. Executive Dashboard ==========
with tab_dash:
    st.markdown("# 💎 Executive Dashboard")
    if not client:
        st.info("Connect BigQuery (service-key.json and dataset) to see metrics, revenue charts, and Sentinel health.")
    else:
        # --- Anomaly: show FIRST if detected (Revenue -10% and Expense +10%) ---
        anomaly = {}
        try:
            anomaly = _cached_get_anomaly(7)
        except Exception:
            pass
        if anomaly.get("detected"):
            st.error(f"⚠️ **ANOMALY DETECTED** — {anomaly.get('msg', '')} Revenue: {anomaly.get('rev_pct')}% | Expenses: {anomaly.get('exp_pct')}% (vs prior 7 days). Review revenue and cost controls.")

        # --- Sync Freshness + Sync Now ---
        freshness = {}
        try:
            freshness = _cached_get_freshness()
        except Exception as e:
            log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
        if freshness.get("expenses", {}).get("stale", True):
            st.warning("⚠️ Warning: Expense data is stale. Please drop new Excel files in Drive.")

        _sync_scripts = [
            ("Sync Expenses", "01_Data_Sync/sync_expenses.py"),
            ("Sync Recipes", "01_Data_Sync/sync_recipes.py"),
            ("Sync Purchases", "01_Data_Sync/sync_purchases.py"),
            ("Sync Cash Ops", "01_Data_Sync/sync_cash_ops.py"),
            ("Sync Wastage", "01_Data_Sync/sync_wastage.py"),
        ]

        def _run_master_sync():
            _env = {**os.environ, "SYNC_TRIGGERED_BY": "master_sync"}
            for _label, _rel in _sync_scripts:
                _p = os.path.join(_PROJECT_ROOT, _rel)
                try:
                    subprocess.run([sys.executable, _p], capture_output=True, text=True, encoding="utf-8", env=_env, cwd=_PROJECT_ROOT, timeout=300)
                except Exception:
                    pass

        with st.expander("🔄 Drive Sync — Sync Now", expanded=False):
            c1, c2 = st.columns([1, 3])
            with c1:
                if st.button("▶️ Master Sync", use_container_width=True, key="btn_master_sync"):
                    with st.spinner("Running all sync scripts..."):
                        _t = threading.Thread(target=_run_master_sync, daemon=True)
                        _t.start()
                        _t.join(timeout=320)
                    st.success("Sync triggered.")
                    st.rerun()
            with c2:
                st.caption("Run individual modules below if needed.")
            freshness = {}
            try:
                freshness = _cached_get_freshness()
            except Exception:
                freshness = {}
            _cols = st.columns(min(5, len(_sync_scripts)))
            for _i, (_label, _rel) in enumerate(_sync_scripts):
                with _cols[_i % len(_cols)]:
                    _stype = _rel.replace("01_Data_Sync/sync_", "").replace(".py", "")
                    _last = freshness.get(_stype, {}).get("last_sync")
                    _last_str = _last.strftime("%Y-%m-%d %H:%M") if _last and hasattr(_last, "strftime") else ("—" if _last is None else str(_last)[:16])
                    _stal = freshness.get(_stype, {}).get("stale", True)
                    if st.button(_label, use_container_width=True, key=f"sync_{_stype}"):
                        _p = os.path.join(_PROJECT_ROOT, _rel)
                        with st.spinner(f"Running {_label}..."):
                            _env = {**os.environ, "SYNC_TRIGGERED_BY": "manual"}
                            _r = subprocess.run([sys.executable, _p], capture_output=True, text=True, encoding="utf-8", env=_env, cwd=_PROJECT_ROOT, timeout=300)
                        if _r.returncode == 0:
                            st.success(f"{_label} done.")
                            st.rerun()
                        else:
                            _err = (_r.stderr or _r.stdout or "")[:500]
                            st.error(f"{_label} failed: {_err}")
                    st.caption(f"Last: {_last_str}" + (" ⚠️ stale" if _stal else ""))

        st.markdown("---")

        # AI Observations (proactive from ai_task_queue)
        obs = []
        try:
            obs = _cached_get_obs(12)
        except Exception as e:
            log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
            st.warning("AI Observations temporarily unavailable.")
        if obs:
            st.markdown("### 🔬 AI Observations")
            ncols = min(4, max(1, len(obs)))
            cols = st.columns(ncols)
            for i, o in enumerate(obs[:8]):
                with cols[i % ncols]:
                    pr = (o.get("priority") or "Medium").lower()
                    cls = "obs-high" if pr == "high" else ("obs-medium" if pr == "medium" else "obs-low")
                    st.markdown(f'<div class="glass-panel"><span class="obs-chip {cls}">{o.get("priority", "—")}</span> <strong>{o.get("title", "—")}</strong><br><small>{o.get("description", "")}</small></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Revenue vs Expenses (Plotly)
        st.markdown("### 📊 Revenue vs Expenses")
        rev_exp = {"dates": [], "revenue": [], "expenses": [], "net": [], "error": None}
        try:
            rev_exp = _cached_get_rev_exp(30)
        except Exception as e:
            log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
            rev_exp["error"] = str(e)
        if rev_exp.get("dates"):
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Revenue", x=rev_exp["dates"], y=rev_exp["revenue"], marker_color="#22c55e"))
            fig.add_trace(go.Bar(name="Expenses", x=rev_exp["dates"], y=rev_exp["expenses"], marker_color="#ef4444"))
            fig.add_trace(go.Scatter(name="Net", x=rev_exp["dates"], y=rev_exp["net"], mode="lines+markers", line=dict(color="#8b5cf6", width=2), yaxis="y2"))
            fig.update_layout(
                barmode="group", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(22,27,34,0.5)",
                font=dict(family="Outfit", color="#e6edf3"), legend=dict(orientation="h", yanchor="bottom", y=1.02),
                xaxis=dict(tickangle=-45), margin=dict(t=60), height=380,
                yaxis=dict(title="Revenue / Expenses"), yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Net")
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue/expense data for the last 30 days. " + (rev_exp.get("error") or ""))

        # Sentinel Task health
        st.markdown("### 🛡️ Sentinel Task Health")
        tasks = []
        try:
            tasks = _cached_get_tasks(15)
        except Exception:
            pass
        if tasks:
            for t in tasks:
                pr = (t.get("priority") or "Medium").lower()
                st.markdown(f"""
                <div class="glass-panel">
                    <span class="obs-chip {'obs-high' if pr=='high' else 'obs-medium' if pr=='medium' else 'obs-low'}">{t.get('priority','—')}</span>
                    <strong>{t.get('task_type','—')}</strong> · {t.get('item_involved','—')}<br>
                    <small>{t.get('description','')}</small><br>
                    <small style="color:#6e7681;">{t.get('created_at','')}</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No pending Sentinel tasks. System healthy.")

# ========== 2. Intelligence Chat ==========
with tab_chat:
    st.markdown("# 🧠 Intelligence Chat")
    if not client:
        st.info("Connect BigQuery to use the AI chat. Configure service-key.json and dataset.")
    else:
        try:
            from utils.enhanced_chat import render_enhanced_chat_interface
            render_enhanced_chat_interface(client, settings, on_assistant_response=maybe_log_logic_gap)
        except ImportError:
            try:
                from utils.chat_interface import render_chat_interface
                render_chat_interface(client, settings)
            except Exception as e:
                log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
                st.error(f"Chat unavailable: {e}")
        except Exception as e:
            log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
            st.error(f"Chat error: {e}")

# ========== 3. User & Rights ==========
with tab_users:
    if not _can("users"):
        st.warning("You don't have access to this tab. Switch to Admin or Manager in the sidebar.")
    else:
        st.markdown("# 👥 User & Rights")
        st.markdown("JSON-based user DB: username (fixed), phone, email, password, pin, role, permissions. Admins can edit all except username and delete users.")
        roles = get_roles()
        for r, tabs in roles.items():
            with st.expander(f"**{r}**" + (" (full access)" if r == "Admin" else "")):
                for t in tabs:
                    st.caption(f"  ✓ {t}")
        st.markdown("---")
        st.markdown("### Users")
        users = get_users()
        if users:
            for u in users:
                un = u.get("username") or ""
                with st.container():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.caption(f"**{un}** · {u.get('email','')} · {u.get('phone','')} · {u.get('role_tag','')}")
                    with c2:
                        if st.button("Edit", key=f"edit_{un}", use_container_width=True):
                            st.session_state.edit_username = un
                            st.rerun()
                        if st.button("Delete", key=f"del_{un}", use_container_width=True):
                            try:
                                delete_user(un)
                                st.success(f"Deleted {un}")
                                st.rerun()
                            except Exception as ex:
                                st.error(str(ex))
            if st.session_state.get("edit_username"):
                eu = st.session_state.edit_username
                uo = get_user_by_username(eu)
                if uo:
                    with st.expander("✏️ Edit user (username fixed)", expanded=True):
                        st.text_input("Username (read-only)", value=eu, disabled=True, key="ef_username")
                        ef_phone = st.text_input("Phone (10 digits)", value=uo.get("phone",""), key="ef_phone")
                        ef_email = st.text_input("Email", value=uo.get("email",""), key="ef_email")
                        ef_pw = st.text_input("Password", value=uo.get("password",""), type="password", key="ef_pw")
                        ef_pin = st.text_input("PIN", value=uo.get("pin",""), key="ef_pin")
                        _rk = list(roles.keys())
                        _ri = _rk.index(uo.get("role_tag") or "Staff") if (uo.get("role_tag") or "Staff") in _rk else 0
                        ef_role = st.selectbox("Role", _rk, index=_ri, key="ef_role")
                        ef_perms = st.multiselect("Permissions (override)", TAB_KEYS, default=uo.get("permissions") or [], key="ef_perms")
                        if st.button("Save", key="ef_save"):
                            try:
                                update_user(eu, phone=ef_phone, email=ef_email, password=ef_pw or uo.get("password"), pin=ef_pin, role_tag=ef_role, permissions=ef_perms)
                                st.session_state.edit_username = None
                                st.success("Updated.")
                                st.rerun()
                            except Exception as ex:
                                st.error(str(ex))
                        if st.button("Cancel", key="ef_cancel"):
                            st.session_state.edit_username = None
                            st.rerun()
        else:
            st.caption("No users. Add below.")
        with st.expander("➕ Add user"):
            au = st.text_input("Username", key="au_username")
            ap = st.text_input("Phone (10 digits)", key="au_phone")
            ae = st.text_input("Email", key="au_email")
            apw = st.text_input("Password", type="password", key="au_pw")
            api = st.text_input("PIN", key="au_pin")
            ar = st.selectbox("Role", list(roles.keys()), key="au_role")
            aperm = st.multiselect("Permissions (override)", TAB_KEYS, key="au_perms")
            if st.button("Add user", key="add_user") and au:
                try:
                    user_add(au, ap, ae, apw, api, ar, aperm)
                    st.success("Added.")
                    st.rerun()
                except Exception as ex:
                    st.error(str(ex))

# ========== 4. API & Config Center ==========
with tab_config:
    if not _can("api_config"):
        st.warning("You don't have access to this tab. Switch to Admin or Manager in the sidebar.")
    else:
        st.markdown("# ⚙️ API & Config Center")
        st.caption("Update API keys and BQ project without editing code. Changes apply after app restart.")
        # --- Sync Status Matrix [Module, Last Sync (exact timestamp), Data Freshness, Triggered By] ---
        if client:
            try:
                _matrix = get_sync_status_matrix(client, settings)
                if _matrix:
                    with st.expander("📋 Sync Status Matrix", expanded=True):
                        _df = pd.DataFrame(_matrix)
                        _df["Last Sync"] = _df["last_sync_time"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M") if hasattr(x, "strftime") else (str(x)[:16] if x else "—"))
                        _df["Data Freshness"] = _df["data_freshness_label"].fillna("—").astype(str) if "data_freshness_label" in _df.columns else "—"
                        _disp = _df[["module", "Last Sync", "Data Freshness", "triggered_by"]].rename(columns={"module": "Module", "triggered_by": "Triggered By"})
                        st.dataframe(_disp, use_container_width=True, hide_index=True)
                        try:
                            _md = _disp.to_markdown(index=False)
                        except Exception:
                            _md = _disp.to_string(index=False)
                        _csv = _disp.to_csv(index=False)
                        _r1, _r2 = st.columns(2)
                        with _r1:
                            st.download_button("[Copy Markdown]", _md, file_name="sync_status_matrix.md", mime="text/markdown", key="sm_copy_md")
                        with _r2:
                            st.download_button("[Download CSV]", _csv, file_name="sync_status_matrix.csv", mime="text/csv", key="sm_dl_csv")
            except Exception as e:
                st.caption(f"Sync Status Matrix unavailable: {e}")

        if client:
            try:
                _pid = getattr(settings, "PROJECT_ID", "")
                _ds = getattr(settings, "DATASET_ID", "")
                _tbl = getattr(settings, "TABLE_SYSTEM_COST_LOG", "system_cost_log")
                _budget = float(getattr(settings, "BUDGET_MONTHLY_INR", 1000.0) or 1000.0)
                if _pid and _ds and _tbl:
                    with st.expander("💰 Cost Monitor", expanded=False):
                        st.caption("Estimated BigQuery spend based on dry-run bytes processed (approx).")
                        q_mtd = f"""
                        SELECT
                          COALESCE(SUM(estimated_cost_inr), 0) AS mtd_inr,
                          COUNT(*) AS query_count,
                          COUNT(DISTINCT DATE(ts)) AS active_days
                        FROM `{_pid}.{_ds}.{_tbl}`
                        WHERE DATE(ts) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
                        """
                        df_mtd, _ = query_to_df(client, settings, q_mtd, purpose="cost_monitor.mtd", log_cost=False)
                        mtd_inr = float(df_mtd.iloc[0].get("mtd_inr") or 0) if not df_mtd.empty else 0.0
                        query_count = int(df_mtd.iloc[0].get("query_count") or 0) if not df_mtd.empty else 0
                        active_days = int(df_mtd.iloc[0].get("active_days") or 0) if not df_mtd.empty else 0
                        active_days = max(active_days, 1)
                        from datetime import date
                        today = date.today()
                        days_elapsed = today.day
                        days_in_month = (date(today.year + int(today.month == 12), 1 if today.month == 12 else today.month + 1, 1) - date(today.year, today.month, 1)).days
                        projected = (mtd_inr / max(days_elapsed, 1)) * max(days_in_month, 1)
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.metric("Month-to-date (₹)", f"₹{mtd_inr:,.0f}")
                        with c2:
                            st.metric("Projected month (₹)", f"₹{projected:,.0f}")
                        with c3:
                            st.metric("Budget cap (₹)", f"₹{_budget:,.0f}")
                        with c4:
                            st.metric("Queries logged", f"{query_count}")
                        if projected > _budget:
                            st.warning(f"Projected monthly spend ₹{projected:,.0f} exceeds your budget cap ₹{_budget:,.0f}. Consider reducing heavy dashboard refreshes and chat context size.")
                        else:
                            st.success(f"Projected monthly spend ₹{projected:,.0f} is within your budget cap ₹{_budget:,.0f}.")

                        q_top = f"""
                        SELECT purpose,
                               SUM(estimated_cost_inr) AS inr,
                               SUM(bytes_processed) AS bytes,
                               COUNT(*) AS n
                        FROM `{_pid}.{_ds}.{_tbl}`
                        WHERE DATE(ts) >= DATE_TRUNC(CURRENT_DATE(), MONTH)
                        GROUP BY purpose
                        ORDER BY inr DESC
                        LIMIT 15
                        """
                        df_top, _ = query_to_df(client, settings, q_top, purpose="cost_monitor.top", log_cost=False)
                        if not df_top.empty:
                            df_top = df_top.copy()
                            df_top["inr"] = df_top["inr"].fillna(0).astype(float)
                            df_top["bytes"] = df_top["bytes"].fillna(0).astype(float)
                            df_top["GB"] = (df_top["bytes"] / (1024**3)).round(3)
                            disp = df_top[["purpose", "n", "GB", "inr"]].rename(columns={"purpose": "Purpose", "n": "Calls", "inr": "₹ (est.)"})
                            st.dataframe(disp, use_container_width=True, hide_index=True)
                        else:
                            st.info("No cost logs yet. Use Dashboard or Chat to generate activity.")
                else:
                    st.caption("Cost monitor unavailable: missing PROJECT_ID/DATASET_ID or cost log table.")
            except Exception as e:
                st.caption(f"Cost monitor unavailable: {e}")
        cfg = EffectiveSettings()
        with st.form("config_form"):
            project_id = st.text_input("PROJECT_ID", value=cfg.PROJECT_ID, key="c_project")
            dataset_id = st.text_input("DATASET_ID", value=cfg.DATASET_ID, key="c_dataset")
            gemini_key = st.text_input("GEMINI_API_KEY", value=cfg.GEMINI_API_KEY, type="password", key="c_gemini")
            key_file = st.text_input("KEY_FILE (path)", value=getattr(cfg, "KEY_FILE", "service-key.json"), key="c_keyfile")
            pp_key = st.text_input("PP_APP_KEY", value=getattr(cfg, "PP_APP_KEY", ""), type="password", key="c_ppkey")
            pp_secret = st.text_input("PP_APP_SECRET", value=getattr(cfg, "PP_APP_SECRET", ""), type="password", key="c_ppsec")
            pp_token = st.text_input("PP_ACCESS_TOKEN", value=getattr(cfg, "PP_ACCESS_TOKEN", ""), type="password", key="c_pptok")
            if st.form_submit_button("Save to config_override.json"):
                save_config_override({
                    "PROJECT_ID": project_id or None, "DATASET_ID": dataset_id or None,
                    "GEMINI_API_KEY": gemini_key or None, "KEY_FILE": key_file or None,
                    "PP_APP_KEY": pp_key or None, "PP_APP_SECRET": pp_secret or None, "PP_ACCESS_TOKEN": pp_token or None,
                })
                st.success("Saved. Restart the app to use new values.")

# ========== 5. Evolution Lab ==========
with tab_evo:
    if not _can("evolution_lab"):
        st.warning("You don't have access to this tab. Switch to Admin or Manager in the sidebar.")
    elif not client:
        st.info("Connect BigQuery to view and manage evolution suggestions.")
    else:
        st.markdown("# 🧪 Evolution Lab")
        st.caption("Suggestions from Intelligence Chat when it could not answer. Authorize to mark for development.")
        status_filter = st.selectbox("Filter by status", ["all", "proposed", "authorized", "in_progress", "complete"], key="evo_filter")
        st_filter = None if status_filter == "all" else status_filter
        suggestions = []
        try:
            suggestions = get_evolution_suggestions(client, settings, status_filter=st_filter, limit=50)
        except Exception as e:
            log_error("titan_app", str(e), exc_info=sys.exc_info(), client=client, settings_mod=settings, file_path=__file__)
            st.warning("Could not load evolution suggestions.")
        if not suggestions:
            st.info("No evolution suggestions yet. Use Intelligence Chat; when TITAN cannot answer, it will log here.")
        for s in suggestions:
            sid = str(s.get("id") or "")
            ts = s.get("timestamp", "") or ""
            uq = s.get("user_query", "") or ""
            gap = s.get("logic_gap_detected", "") or ""
            spec = s.get("suggested_feature_specification", "") or ""
            status = s.get("development_status", "proposed") or "proposed"
            with st.container():
                st.markdown(f"""
                <div class="glass-panel">
                    <strong>Query</strong> {uq[:200]}{'…' if len(uq)>200 else ''}<br>
                    <strong>Gap</strong> {gap[:300]}{'…' if len(gap)>300 else ''}<br>
                    <strong>Spec</strong> {spec[:400]}{'…' if len(spec)>400 else ''}<br>
                    <small>Status: {status} · {ts}</small>
                </div>
                """, unsafe_allow_html=True)
                if status == "proposed" and sid:
                    if st.button("✅ Authorize to build", key=f"auth_{sid}"):
                        try:
                            update_development_status(client, settings, sid, "authorized")
                            st.success("Status set to authorized.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6e7681; padding: 1rem; font-family: 'Outfit', sans-serif;">
    🚀 <strong>Titan ERP</strong> · Self-Developing Intelligence · Cafe Mellow · Tiruppur, Tamil Nadu
</div>
""", unsafe_allow_html=True)
