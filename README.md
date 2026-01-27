# 🛡️ TITAN ERP - Universal Semantic Brain Edition

**v4.0 Production** | January 2026 | AGI for Data Engineering

---

## 🎯 What is TITAN?

TITAN is an **AI-powered Business Intelligence Platform** with a revolutionary **Universal Semantic Brain** that:

- **Understands ANY data** automatically without predefined rules (2 Crore+ scenarios)
- **Auto-classifies** into 15+ business categories with confidence scoring
- **Multi-tenant SaaS** architecture supporting 1 Lakh+ subscribers
- **Immutable Event Ledger** for complete audit trails
- **AI CFO Chat** that speaks in numbers and action items
- **360° Cross-Category Analysis** for executive insights

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.x installed
- Google Cloud service account with BigQuery access
- Gemini API key from Google AI Studio

### First-Time Setup
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env  # Edit with your credentials

# 3. Start API server
uvicorn api.main:app --port 8000

# 4. Start web interface (new terminal)
cd web
npm install
npm run dev

# 5. Access TITAN
# CEO Chat: http://localhost:3000/chat
# Settings: http://localhost:3000/settings
# Admin:    http://localhost:8501 (streamlit run titan_app.py)
```

---

## 🏗️ Tech Stack

### Backend
- **Framework:** FastAPI (REST API) + Streamlit (Admin Dashboard)
- **Language:** Python 3.x
- **Database:** Google BigQuery (serverless data warehouse)
- **AI Engine:** Google Gemini 2.0 Flash
- **POS Integration:** Petpooja API

### Frontend
- **Framework:** Next.js 16.1.4 (App Router)
- **UI:** React 19.2.3 + TailwindCSS 4.x
- **Language:** TypeScript 5.x

### External Services
- Google Drive API (document storage)
- Google Cloud BigQuery (analytics)
- Gemini AI (intelligence layer)

---

## 📁 Project Structure

```
Cafe_AI/
├── api/                      # FastAPI REST endpoints
│   └── main.py               # Primary adapter (1300 lines)
│
├── pillars/                  # Domain logic (Hexagonal Core)
│   ├── chat_intel.py         # AI conversation intelligence
│   ├── dashboard.py          # Revenue/expense analytics
│   ├── expense_analysis_engine.py
│   ├── users_roles.py        # RBAC implementation
│   ├── config_vault.py       # Configuration management
│   ├── evolution.py          # Self-improvement tracking
│   └── system_logger.py      # Centralized logging
│
├── 01_Data_Sync/             # Secondary adapters (ETL)
│   ├── sync_sales_raw.py     # Petpooja POS sync
│   ├── sync_expenses.py      # Google Drive expense sync
│   ├── sync_purchases.py
│   ├── sync_recipes.py
│   └── sync_wastage.py
│
├── utils/                    # Application services
│   ├── bq_guardrails.py      # Budget protection & cost estimation
│   ├── gemini_chat.py        # AI orchestration
│   ├── enhanced_chat.py      # Streaming chat interface
│   ├── ops_brief.py          # Daily operational reports
│   └── ai_task_queue.py      # Proactive task generation
│
├── 04_Intelligence_Lab/      # AI/Analytics layer
│   ├── sentinel_hub.py       # Health monitoring orchestrator
│   ├── titan_dna.py          # System self-analysis
│   └── pillars/              # Audit modules
│       ├── p1_revenue_integrity.py
│       ├── p2_inventory_gap.py
│       └── p3_expense_purity.py
│
├── web/                      # Next.js frontend
│   └── src/
│       ├── app/dashboard/    # Metrics dashboard
│       ├── app/chat/         # AI chat interface
│       ├── app/operations/   # Operations view
│       └── app/settings/     # Configuration UI
│
├── scheduler/                # Automation
│   └── daily_automation.py
│
├── scripts/                  # DevOps utilities
│   └── generate_system_map.py # Living documentation
│
├── settings.py               # ⭐ Configuration vault
├── titan_app.py              # Streamlit admin dashboard
└── requirements.txt          # Python dependencies
```

---

## ⚙️ Configuration

### Environment Variables (Recommended)
Create a `.env` file in the project root:

```bash
# Google Cloud
PROJECT_ID=your-project-id
DATASET_ID=cafe_operations
KEY_FILE=service-key.json

# AI Engine
GEMINI_API_KEY=your-gemini-api-key

# Petpooja POS API
PP_APP_KEY=your-petpooja-app-key
PP_APP_SECRET=your-petpooja-secret
PP_ACCESS_TOKEN=your-access-token
PP_MAPPING_CODE=your-mapping-code

# Google Drive Folder IDs
FOLDER_ID_EXPENSES=your-drive-folder-id
FOLDER_ID_CASH_OPS=your-drive-folder-id
FOLDER_ID_RECIPES=your-drive-folder-id
FOLDER_ID_PURCHASES=your-drive-folder-id
FOLDER_ID_WASTAGE=your-drive-folder-id

# Budget Guardrails
BUDGET_MONTHLY_INR=1000
MAX_QUERY_COST_INR=10
```

### Google Drive Setup
Share each Drive folder with your service account email (Viewer permission):
- Find the email in `service-key.json` → `client_email` field
- Example: `python-admin@your-project.iam.gserviceaccount.com`

---

## 🔄 Daily Operations Workflow

### Phase 1: Data Synchronization
```bash
# Sync sales data from Petpooja
python 01_Data_Sync/sync_sales_raw.py

# Parse sales JSON into structured data
python 01_Data_Sync/titan_sales_parser.py

# Sync expense reports from Google Drive
python 01_Data_Sync/sync_expenses.py

# Sync recipe/BOM data
python 01_Data_Sync/sync_recipes.py

# Optional: Run all syncs via Dashboard "Master Sync" button
```

### Phase 2: Intelligence Scan
```bash
# Run health monitoring and anomaly detection
python 04_Intelligence_Lab/sentinel_hub.py

# This automatically:
# - Scans all pillars in pillars/ directory
# - Detects revenue anomalies, inventory gaps, expense issues
# - Uploads findings to ai_task_queue table
```

### Phase 3: Access Dashboards
```bash
# Admin Dashboard (Streamlit)
streamlit run titan_app.py
# → http://localhost:8501

# Modern Web Interface (Next.js)
cd web && npm run dev
# → http://localhost:3000
```

---

## 🧠 AI Chat Interface - Example Queries

### Financial Analysis
- "What were my expenses yesterday?"
- "Show me cash expenses for last week excluding personal items"
- "Calculate profit and loss for last month"
- "What's my net profit margin?"

### Staff & Payroll
- "How much advance did Arun get last month?"
- "When did I pay Arun salary?"
- "Show me all staff-related expenses"

### Product Intelligence
- "What are my top selling items this week?"
- "Why is cheesecake sales dropping?"
- "Should I discontinue cupcakes based on performance?"
- "Compare truffle pastry sales month-over-month"

### Operational Insights
- "Give me today's business summary"
- "What should I focus on today?"
- "Show me revenue by delivery partner"
- "Detect any inventory gaps in my recipes"

---

## 🏛️ Architecture (Hexagonal/Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────────┐
│                  PRIMARY ADAPTERS (Inbound)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Next.js   │  │  FastAPI    │  │  Streamlit  │             │
│  │  Frontend   │  │   REST API  │  │   Admin UI  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION SERVICES                          │
│  • Chat Interface  • Query Engine  • BigQuery Guardrails        │
│  • AI Task Queue   • Ops Brief Generator                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN LOGIC (PILLARS)                        │
│  • Config Vault    • Dashboard Analytics  • Users & Roles       │
│  • Chat Intelligence  • System Logger  • Evolution Engine       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SECONDARY ADAPTERS (Outbound)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │  BigQuery   │  │ Google Drive │  │  Petpooja   │            │
│  │  Warehouse  │  │   Storage    │  │     POS     │            │
│  └─────────────┘  └──────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌──────────────┐                              │
│  │   Gemini    │  │  Sync Jobs   │                              │
│  │     AI      │  │  (ETL/ELT)   │                              │
│  └─────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 BigQuery Tables (Data Schema)

### Revenue Domain
- `sales_raw_layer` - Raw POS JSON from Petpooja
- `sales_items_parsed` - Parsed line items
- `sales_enhanced` - Enriched with customer/delivery metadata

### Expense Domain
- `expenses_master` - Category-based expense tracking
- `cash_flow_master` - Withdrawals/topups
- `purchases_master` - Ingredient procurement

### Inventory Domain
- `ingredients_master` - Raw materials
- `recipes_sales_master` - Item composition (BOM)
- `recipes_production_master` - Sub-recipe assembly
- `wastage_log` - Loss tracking

### System Domain
- `dev_evolution_log` - Self-improvement tracking
- `system_error_log` - Error logging
- `system_sync_log` - ETL status
- `system_cost_log` - BigQuery spend tracking
- `ai_task_queue` - Proactive alerts from Sentinel Hub

---

## 🛡️ Security Features

### Credential Management
- Environment variables via `os.getenv()` (best practice)
- Service account authentication for Google Cloud
- Config override system (`config_override.json`)
- **⚠️ CRITICAL:** Never commit `service-key.json` or `.env` to version control

### Budget Protection
- **BigQuery Guardrails:** Dry-run cost estimation before query execution
- **Monthly Budget Cap:** Default ₹1,000/month (configurable)
- **Query-level Cost Logging:** Track spend by purpose
- **Budget Breach Prevention:** Blocks queries exceeding threshold

### Data Flow Security
1. **Inbound:** CORS-protected FastAPI endpoints
2. **Outbound:** OAuth2 for Google APIs, token-based for Petpooja
3. **Storage:** BigQuery with service account authentication

---

## 🧪 Intelligence & Monitoring

### Sentinel Hub (Automated Health Checks)
Monitors:
- **Revenue Anomalies:** >10% deviation from baseline
- **Data Freshness:** Stale sync warnings (>24h)
- **Expense Spikes:** Unusual spending patterns
- **Inventory Gaps:** Sales items without recipes

### Self-Evolution System
The system tracks its own improvements in `dev_evolution_log`:
- Feature additions suggested by AI
- Bug fixes identified by Sentinel
- Performance optimizations
- User feedback integration

---

## 📈 API Endpoints (FastAPI)

### Core Endpoints
- `GET /health` - System health check
- `POST /chat` - AI chat (non-streaming)
- `POST /chat/stream` - AI chat with SSE streaming
- `GET /config` - Configuration status
- `POST /config` - Update configuration

### Metrics & Analytics
- `GET /metrics/overview` - Revenue/expense summary
- `GET /ops/brief/today` - Daily operational brief
- `GET /ops/sales/channels` - Sales by delivery partner
- `GET /ops/sales/top-items` - Top-selling items

### Admin
- `GET /tasks/generate` - Generate AI tasks from brief
- `POST /ops/brief/generate` - Force-generate new brief

Full API documentation: http://localhost:8000/docs (when server is running)

---

## 🎯 Key Features

### ✅ Implemented
- Multi-chat AI sessions with BigQuery memory
- Real-time revenue vs. expense analytics
- Automated task generation from data anomalies
- Recipe completeness validation
- Wastage analysis and tracking
- User role-based access control (RBAC)
- Cost-aware BigQuery query execution
- Streaming chat responses (SSE)
- Multi-tenant ready architecture

### ⏳ Roadmap
- Multi-tenant isolation (row-level security)
- Recipe intelligence (auto-detect usage anomalies)
- Predictive demand forecasting
- Mobile app (React Native)
- Real-time Petpooja webhook integration

---

## 🛠️ Developer Commands

```bash
# Generate system blueprint documentation
python scripts/generate_system_map.py

# Update system DNA (after adding pillars)
python 04_Intelligence_Lab/titan_dna.py

# Run health scan
python 04_Intelligence_Lab/titan_dna_pulse.py > dna_report.txt

# Check system errors
cat logs/titan_system_log.txt

# Run all sync scripts
# (Use Dashboard "Master Sync" button or run individually)
```

---

## 🚨 Troubleshooting

### BigQuery Connection Issues
- Verify `service-key.json` exists and is valid
- Check service account has BigQuery Data Editor role
- Confirm `PROJECT_ID` and `DATASET_ID` in settings

### Drive Sync Failures
- Ensure Drive folders are shared with service account email
- Check folder IDs in `settings.py` are correct
- Verify files have proper headers (Amount column for expenses)

### Dashboard Errors
- Check `logs/titan_system_log.txt` for detailed error traces
- Query `system_error_log` table in BigQuery
- Run `titan_integrity.py` for system health check

### Cost Budget Exceeded
- Review cost logs: `SELECT * FROM system_cost_log ORDER BY ts DESC`
- Adjust `BUDGET_MONTHLY_INR` in settings
- Use `DISABLE_BUDGET_BREAKER=true` to bypass (not recommended)

---

## 📚 Additional Documentation

- **BLUEPRINT.md** - Auto-generated system architecture map
- **PROJECT_FLOW_EXPLANATION.md** - Deep technical flow details
- **COMPLETE_IMPLEMENTATION_SUMMARY.md** - Implementation status
- **TITAN_VISION_ROADMAP.md** - Product roadmap
- **DEPLOY.md** - Deployment guide
- **EXPENSES_MODULE_SPEC.md** - Expense tracking specifications

---

## 🎓 Getting Started Guide

### For New Developers
1. Read this README completely
2. Run `python 04_Intelligence_Lab/titan_dna.py` to understand system structure
3. Generate system blueprint: `python scripts/generate_system_map.py`
4. Launch dashboard and explore: `streamlit run titan_app.py`

### For System Administrators
1. Configure `.env` file with credentials
2. Set up Google Drive folder sharing
3. Run initial data sync scripts
4. Schedule daily automation: `python scheduler/daily_automation.py`

### For Data Analysts
1. Access Next.js interface at http://localhost:3000
2. Use AI chat for natural language queries
3. Download operational briefs from Dashboard
4. Query BigQuery directly for custom analysis

---

## 🤝 Contributing

### Adding New Audit Logic (Pillars)
1. Create `04_Intelligence_Lab/pillars/p4_your_audit.py`
2. Implement `run_audit(client, settings)` function
3. Return list of findings (dict format)
4. Run `sentinel_hub.py` - automatic discovery!

### Adding New Data Syncs
1. Create `01_Data_Sync/sync_your_source.py`
2. Follow existing sync script patterns
3. Update `system_sync_log` on success
4. Add to Dashboard sync buttons

---

## 📞 System Status

**Core Features:** ✅ Operational  
**AI Chat:** ✅ Streaming  
**Query Engine:** ✅ Cost-Protected  
**Reports:** ✅ Auto-Generated  
**Sentinel:** ✅ Monitoring  
**Multi-Tenant:** ⏳ In Progress

---

## 🔐 Security Notice

**⚠️ IMPORTANT:** This codebase contains sensitive credential patterns. Before deploying:

1. ✅ Ensure `service-key.json` is in `.gitignore`
2. ✅ Use environment variables for all secrets
3. ✅ Never commit `.env` files
4. ✅ Rotate API keys if repository was ever public
5. ✅ Use Google Secret Manager in production

---

**Built with ❤️ by the TITAN Evolution Engine**  
**Last Updated:** 2026-01-25  
**Version:** 5.0.0 (Hexagonal Architecture + Next.js)  
**License:** Proprietary (Ever Built SaaS)

🚀 **Ready to start?** Run `streamlit run titan_app.py` and access http://localhost:8501
