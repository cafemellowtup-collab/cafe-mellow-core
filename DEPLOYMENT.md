# 🚀 TITAN ERP - Production Deployment Guide

**Architectural Reset Edition** | January 2026 | 200% Deployment Ready

---

## 📋 Pre-Deployment Checklist

### 1. Environment Files
```bash
# ❌ NEVER commit these files:
service-key.json        # Google Cloud service account
config_override.json    # Runtime secrets
.env                    # Environment variables
```

### 2. Required Credentials
| Credential | Where to Get | Required |
|------------|--------------|----------|
| `PROJECT_ID` | Google Cloud Console | ✅ Yes |
| `DATASET_ID` | BigQuery Console | ✅ Yes |
| `KEY_FILE` | GCP Service Account JSON | ✅ Yes |
| `GEMINI_API_KEY` | Google AI Studio | ✅ Yes |
| `PP_APP_KEY` | Petpooja Dashboard | Optional |
| `PP_APP_SECRET` | Petpooja Dashboard | Optional |
| `PP_ACCESS_TOKEN` | Petpooja Dashboard | Optional |
| `PP_MAPPING_CODE` | Petpooja Restaurant ID | Optional |
| `FOLDER_ID_*` | Google Drive Folder URLs | ✅ Recommended |

---

## 🖥️ Terminal Start Commands

### Option A: Full Production Stack (Recommended)
```powershell
# Terminal 1: FastAPI Backend
cd c:\Users\USER\OneDrive\Desktop\Cafe_AI
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Next.js Frontend
cd c:\Users\USER\OneDrive\Desktop\Cafe_AI\web
npm run build
npm start

# Terminal 3: Streamlit Admin (Optional)
cd c:\Users\USER\OneDrive\Desktop\Cafe_AI
streamlit run titan_app.py --server.port 8501
```

### Option B: Development Mode
```powershell
# Backend with auto-reload
uvicorn api.main:app --reload --port 8000

# Frontend with hot-reload
cd web && npm run dev
```

### Option C: Quick Start Script
```powershell
# Create a startup script: start_titan.ps1
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\USER\OneDrive\Desktop\Cafe_AI'; uvicorn api.main:app --port 8000" -PassThru
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\USER\OneDrive\Desktop\Cafe_AI\web'; npm run dev" -PassThru
Write-Host "TITAN ERP Started!"
Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TITAN ERP ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │   Next.js   │    │   FastAPI   │    │  Streamlit  │                │
│  │  Port 3000  │───▶│  Port 8000  │◀───│  Port 8501  │                │
│  │   (CEO UI)  │    │  (REST API) │    │  (Admin UI) │                │
│  └──────┬──────┘    └──────┬──────┘    └─────────────┘                │
│         │                  │                                           │
│         ▼                  ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    CORE SERVICES                                 │  │
│  │  • TITAN CFO Chat Engine (Gemini 2.0 Flash)                     │  │
│  │  • Universal Ingester (50-row Hybrid Parser + Vision)           │  │
│  │  • BigQuery Guardrails (Cost Protection)                        │  │
│  │  • Config Vault (PATCH/Merge Settings)                          │  │
│  └──────────────────────────┬──────────────────────────────────────┘  │
│                             │                                          │
│         ┌───────────────────┼───────────────────┐                     │
│         ▼                   ▼                   ▼                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│  │  BigQuery   │    │Google Drive │    │  Petpooja   │               │
│  │  Warehouse  │    │  (5 folders)│    │    POS      │               │
│  └─────────────┘    └─────────────┘    └─────────────┘               │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Google Drive Folder Setup

### Folder Structure
```
Google Drive/
├── Titan_Expenses/          # Upload expense reports here
├── Titan_Purchases/         # Upload purchase orders here
├── Titan_Inventory/         # Upload inventory counts here
├── Titan_Recipes/           # Upload recipe BOMs here
├── Titan_Wastage/           # Upload wastage logs here
├── Titan_Archived/          # Auto-moved after successful ingestion
└── Titan_Failed/            # Auto-moved after failed ingestion
```

### Sharing Instructions
1. Get your service account email from `service-key.json` → `client_email`
2. Share each folder with the service account (Viewer permission minimum)
3. Copy folder IDs from URLs: `https://drive.google.com/drive/folders/{FOLDER_ID}`
4. Enter folder IDs in Settings UI or `.env`

---

## 🔐 Security Configuration

### Environment Variables (.env)
```bash
# Google Cloud
PROJECT_ID=your-project-id
DATASET_ID=cafe_operations
KEY_FILE=service-key.json

# AI Engine
GEMINI_API_KEY=AIza...

# Petpooja POS (optional)
PP_APP_KEY=your-key
PP_APP_SECRET=your-secret
PP_ACCESS_TOKEN=your-token
PP_MAPPING_CODE=restaurant-id

# Google Drive Folders
FOLDER_ID_EXPENSES=1abc...
FOLDER_ID_PURCHASES=1def...
FOLDER_ID_INVENTORY=1ghi...
FOLDER_ID_RECIPES=1jkl...
FOLDER_ID_WASTAGE=1mno...

# Titan Archive Folders (for folder_watcher.py)
TITAN_ARCHIVED_EXPENSES=1pqr...
TITAN_FAILED_EXPENSES=1stu...

# Budget Protection
BUDGET_MONTHLY_INR=1000
MAX_QUERY_COST_INR=10
```

### Security Best Practices
1. **Never commit secrets** - All sensitive files are in `.gitignore`
2. **Use PATCH for settings** - Prevents credential overwrites
3. **Service account isolation** - Use dedicated SA for each environment
4. **Rotate keys regularly** - Especially after any exposure

---

## ⏰ Automated Cron Jobs

### Folder Watcher (Hourly Ingestion)
```powershell
# Windows Task Scheduler
# Trigger: Daily, repeat every 1 hour
# Action: python scheduler/folder_watcher.py

# Or run manually:
python scheduler/folder_watcher.py
```

### Daily Automation
```powershell
# Full daily sync (sales, expenses, recipes)
python scheduler/daily_automation.py
```

---

## 🧪 Verification Steps

### 1. Backend Health
```powershell
curl http://localhost:8000/health
# Expected: {"ok":true,"bq_connected":true,...}
```

### 2. Config Status
```powershell
curl http://localhost:8000/config
# Expected: All *_set fields should be true
```

### 3. Chat Test
```powershell
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"message\":\"What was yesterday's revenue?\"}"
```

### 4. Frontend Access
- Open http://localhost:3000
- Navigate to Chat → Use CEO Command Chips
- Navigate to Settings → Verify all credentials show "Set"

---

## 🚨 Troubleshooting

### Backend won't start
```powershell
# Check Python dependencies
pip install -r requirements.txt

# Verify service key exists
Test-Path service-key.json
```

### Frontend build fails
```powershell
cd web
rm -r node_modules .next
npm install
npm run build
```

### BigQuery connection errors
1. Verify `service-key.json` is valid
2. Check service account has BigQuery Data Editor role
3. Confirm PROJECT_ID and DATASET_ID match

### Chat returns errors
1. Check GEMINI_API_KEY is set in Settings
2. Verify API key is valid at https://aistudio.google.com
3. Check rate limits aren't exceeded

---

## 📊 Monitoring

### BigQuery Cost Tracking
```sql
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.system_cost_log`
ORDER BY ts DESC LIMIT 50;
```

### Folder Watcher Logs
```sql
SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.folder_watcher_log`
ORDER BY run_timestamp DESC LIMIT 20;
```

---

**Built with TITAN CFO Intelligence** | 200% Deployment Ready | January 2026
