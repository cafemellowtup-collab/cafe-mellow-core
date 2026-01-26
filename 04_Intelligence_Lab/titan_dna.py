"""
TITAN DNA: Living documentation sync. Scans pillars, root .md files, and keeps
TITAN_DNA.json + SYSTEM_README.md in sync with the codebase. Run after any structural change.
"""
import json
import os
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Root = project root (parent of 04_Intelligence_Lab)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Current Mission: change when focus shifts (New Engineer context)
CURRENT_MISSION = (
    "Production-ready TITAN Command Center: 5-tab UI (Executive Dashboard, Intelligence Chat, "
    "User & Rights, API & Config, Evolution Lab), system error logging (file + BigQuery), "
    "DNA-driven docs, and continuous evolution via dev_evolution_log."
)

# Root .md to treat as active (others can be reported as archived or legacy)
ACTIVE_ROOT_MD = {
    "SYSTEM_README.md",
    "PROJECT_FLOW_EXPLANATION.md",
    "COMPLETE_IMPLEMENTATION_SUMMARY.md",
    "START_HERE.md",
    "TITAN_VISION_ROADMAP.md",
    "README_MASTER.md",
    "GETTING_STARTED.md",
}

# 99_Archive paths to skip when scanning "root" .md
EXCLUDE_DIRS = {".venv", "venv", "node_modules", "__pycache__", "99_Archive_Legacy", ".git"}


def _is_excluded(p):
    return any(part in EXCLUDE_DIRS for part in os.path.normpath(p).split(os.sep))


def _scan_root_md():
    out = []
    for f in os.listdir(ROOT):
        if not f.endswith(".md"):
            continue
        fp = os.path.join(ROOT, f)
        if not os.path.isfile(fp) or _is_excluded(fp):
            continue
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
        except Exception:
            mtime = ""
        status = "active" if f in ACTIVE_ROOT_MD else "legacy"
        out.append({"file": f, "status": status, "last_modified": mtime})
    return sorted(out, key=lambda x: x["file"])


def _scan_sentinel_pillars():
    p = os.path.join(ROOT, "04_Intelligence_Lab", "pillars")
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.endswith(".py") and f != "__init__.py"]


def _scan_app_pillars():
    p = os.path.join(ROOT, "pillars")
    if not os.path.isdir(p):
        return []
    return [f for f in os.listdir(p) if f.endswith(".py") and f != "__init__.py"]


def _archived_md():
    """Collect .md files under 99_Archive_Legacy for DNA report."""
    arch = os.path.join(ROOT, "99_Archive_Legacy")
    if not os.path.isdir(arch):
        return []
    out = []
    for r, _d, fs in os.walk(arch):
        for f in fs:
            if f.endswith(".md"):
                rel = os.path.relpath(os.path.join(r, f), ROOT).replace("\\", "/")
                out.append(rel)
    return sorted(out)


def generate_dna_and_readme():
    print("TITAN DNA: SYNCING SYSTEM STATE...")

    sentinel = _scan_sentinel_pillars()
    app_pillars = _scan_app_pillars()
    root_md = _scan_root_md()
    archived_md = _archived_md()

    dna = {
        "project_identity": "TITAN ERP - Cafe Mellow",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "current_mission": CURRENT_MISSION,
        "infrastructure": {
            "editor": "Cursor AI-Native",
            "database": "Google BigQuery",
            "framework": "Modular Pillar Architecture",
        },
        "sentinel_pillars": sentinel,
        "app_pillars": app_pillars,
        "root_markdown": root_md,
        "archived_markdown": archived_md,
        "rules": [
            "Expense tagging: Ledger - Category",
            "Automatic Task Queue injection for anomalies",
            "Purity filter for personal/business separation",
            "All runtime errors to logs/titan_system_log.txt and system_error_log (BQ)",
        ],
    }

    with open(os.path.join(ROOT, "TITAN_DNA.json"), "w", encoding="utf-8") as f:
        json.dump(dna, f, indent=4)

    # SYSTEM_README: Current Mission at top, then state
    readme = f"""# PROJECT TITAN: MISSION CONTROL
**Auto-Generated:** {dna["last_updated"]}

## 🎯 Current Mission
{CURRENT_MISSION}

## 📊 Current System State
- **Sentinel pillars:** {len(sentinel)} ({", ".join(sentinel) or "none"})
- **App pillars:** {len(app_pillars)} ({", ".join(app_pillars) or "none"})
- **Root .md (active):** {len([m for m in root_md if m["status"] == "active"])}

## 🏗️ Architecture
- **Sentinel** (`04_Intelligence_Lab/pillars/`): {chr(10).join([f"  - {p}" for p in sentinel]) or "  (none)"}
- **App** (`pillars/`): {chr(10).join([f"  - {p}" for p in app_pillars]) or "  (none)"}

## 📄 Root Markdown (status)
{chr(10).join([f"- **{m['file']}**: {m['status']} ({m['last_modified']})" for m in root_md])}

## ⚖️ Operational Rules
{chr(10).join([f"- {r}" for r in dna["rules"]])}

---
*Managed by `04_Intelligence_Lab/titan_dna.py`. Run after structural changes.*
"""
    with open(os.path.join(ROOT, "SYSTEM_README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    print("✅ DNA & SYSTEM_README RECONCILED. TITAN_DNA.json and root .md status are live.")


if __name__ == "__main__":
    generate_dna_and_readme()
