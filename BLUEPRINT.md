# 🧬 TITAN ERP - System Blueprint
**Generated:** 2026-01-25 15:23:14  
**Total Code Files Analyzed:** 68  
**Architecture:** Hexagonal (Ports & Adapters) + Multi-Tenant SaaS  

---


## 📊 Data Flow Architecture (Hexagonal/Ports & Adapters)

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRIMARY ADAPTERS (Inbound)                  │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Next.js   │    │  FastAPI    │    │  Streamlit  │         │
│  │  Frontend   │    │   REST API  │    │   Admin UI  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION SERVICES                          │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Chat Interface      • Query Engine                      │ │
│  │  • AI Task Queue       • BigQuery Guardrails              │ │
│  │  • Ops Brief Generator • Performance Optimizer            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOMAIN LOGIC (PILLARS)                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Config Vault        • Dashboard Analytics              │ │
│  │  • Users & Roles       • Chat Intelligence                │ │
│  │  • System Logger       • Evolution Engine                 │ │
│  │  • Expense Analysis    • Revenue Integrity                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SECONDARY ADAPTERS (Outbound)                   │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐            │
│  │  BigQuery   │  │ Google Drive │  │  Petpooja   │            │
│  │  Warehouse  │  │   Storage    │  │     POS     │            │
│  └─────────────┘  └──────────────┘  └─────────────┘            │
│                                                                   │
│  ┌─────────────┐  ┌──────────────┐                              │
│  │   Gemini    │  │  Sync Jobs   │                              │
│  │     AI      │  │  (ETL/ELT)   │                              │
│  └─────────────┘  └──────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```


---

## 🏗️ Architecture Layers

### 1. Domain Logic (Core Business Rules)
**Location:** `pillars/`  
**Purpose:** Pure business logic, framework-agnostic

| File | Purpose | Key Dependencies |
|------|---------|------------------|
| `p1_revenue_integrity.py` | Business Logic | from datetime import datetime, import json |
| `p2_inventory_gap.py` | Business Logic | from datetime import datetime |
| `p3_expense_purity.py` | Business Logic | from datetime import datetime |
| `chat_intel.py` | Business Logic | import re, from datetime import date, from .evolution import log_logic_gap |
| `config_vault.py` | Business Logic | import json, import os, import types |
| `dashboard.py` | Business Logic | import sys, import os, import pandas as pd |
| `evolution.py` | Business Logic | from datetime import datetime, import uuid, from google.cloud import bigquery |
| `expense_analysis_engine.py` | Business Logic | import re, import difflib, from datetime import date, timedelta |
| `system_logger.py` | Business Logic | import os, import sys, import traceback |
| `users_roles.py` | Business Logic | import json, import os, import re |
| `__init__.py` | Business Logic | from .evolution import ensure_dev_evolution_table, log_logic_gap, get_evolution_suggestions, update_development_status, from .dashboard import get_revenue_expenses_data, get_sentinel_health, get_ai_observations, from .config_vault import EffectiveSettings, load_config_override, save_config_override |

### 2. Primary Adapters (User-Facing Interfaces)
**Location:** `api/`, `web/`, `titan_app.py`  
**Purpose:** REST APIs, UI components, user interaction

| File | Purpose | Language |
|------|---------|----------|
| `api/main.py` | AI/Intelligence Service | Python |
| `api/__init__.py` | Utility/Helper | Python |

### 3. Secondary Adapters (External Systems)
**Location:** `01_Data_Sync/`  
**Purpose:** Integration with BigQuery, Drive, Petpooja, AI APIs

| File | Purpose | Data Source |
|------|---------|-------------|
| `enhanced_sales_parser.py` | Utility/Helper | External API |
| `header_utils.py` | Utility/Helper | External API |
| `sync_cash.py` | Data Synchronization (ETL) | External API |
| `sync_cash_ops.py` | Data Synchronization (ETL) | External API |
| `sync_expenses.py` | Data Synchronization (ETL) | External API |
| `sync_ingredients.py` | Data Synchronization (ETL) | External API |
| `sync_production.py` | Data Synchronization (ETL) | External API |
| `sync_purchases.py` | Data Synchronization (ETL) | External API |
| `sync_recipes.py` | Data Synchronization (ETL) | External API |
| `sync_sales_raw.py` | Data Synchronization (ETL) | External API |
| `sync_wastage.py` | Data Synchronization (ETL) | External API |
| `titan_sales_parser.py` | Utility/Helper | External API |

### 4. Application Services
**Location:** `utils/`  
**Purpose:** Cross-cutting concerns, query engines, AI orchestration

| File | Purpose | Layer |
|------|---------|-------|
| `advanced_ai_engine.py` | AI/Intelligence Service | Service |
| `advanced_query_engine.py` | Utility/Helper | Service |
| `ai_agent.py` | AI/Intelligence Service | Service |
| `ai_task_queue.py` | AI/Intelligence Service | Service |
| `bq_guardrails.py` | AI/Intelligence Service | Service |
| `chat_interface.py` | AI/Intelligence Service | Service |
| `daily_reporter.py` | AI/Intelligence Service | Service |
| `data_optimizer.py` | Utility/Helper | Service |
| `enhanced_chat.py` | AI/Intelligence Service | Service |
| `gemini_chat.py` | AI/Intelligence Service | Service |
| `market_intelligence.py` | AI/Intelligence Service | Service |
| `ops_brief.py` | Utility/Helper | Service |
| `performance_optimizer.py` | Utility/Helper | Service |
| `schema_analyzer.py` | Utility/Helper | Service |
| `task_manager.py` | Utility/Helper | Service |
| `ui_components.py` | UI Component | Service |
| `__init__.py` | Utility/Helper | Service |

### 5. Intelligence Layer (AI/Analytics)
**Location:** `04_Intelligence_Lab/`  
**Purpose:** Sentinel monitoring, DNA analysis, evolution tracking

| File | Purpose | Type |
|------|---------|------|
| `generate_session_starter.py` | Utility/Helper | AI/Analytics |
| `sentinel_hub.py` | Utility/Helper | AI/Analytics |
| `titan_dna.py` | Utility/Helper | AI/Analytics |
| `titan_dna_pulse.py` | Utility/Helper | AI/Analytics |

### 6. Frontend (Next.js SaaS Interface)
**Location:** `web/src/`  
**Purpose:** Multi-tenant web interface

| Component | Purpose | Framework |
|-----------|---------|-----------|
| `layout.tsx` | Utility/Helper | TypeScript React |
| `page.tsx` | UI Component | TypeScript React |
| `ChatClient.tsx` | UI Component | TypeScript React |
| `page.tsx` | UI Component | TypeScript React |
| `DashboardClient.tsx` | UI Component | TypeScript React |
| `page.tsx` | UI Component | TypeScript React |
| `OperationsClient.tsx` | UI Component | TypeScript React |
| `page.tsx` | UI Component | TypeScript React |
| `page.tsx` | UI Component | TypeScript React |
| `SettingsClient.tsx` | UI Component | TypeScript React |
| `AppShell.tsx` | Utility/Helper | TypeScript React |
| `api.ts` | REST API Endpoint | TypeScript |

---

## 🔐 Security Architecture

### Credential Management
- **Service Account:** `service-key.json` (Google Cloud)
- **API Keys:** Environment variables via `os.getenv()` in `settings.py`
- **Secret Storage:** `config_override.json` for runtime overrides
- **⚠️ WARNING:** Never commit `service-key.json` or `.env` files to version control

### Data Flow Security
1. **Inbound:** CORS-protected FastAPI endpoints
2. **Outbound:** OAuth2 for Google APIs, token-based for Petpooja
3. **Storage:** BigQuery with service account authentication
4. **AI:** Gemini API key via environment variable

---

## 📦 Domain Models (Business Entities)

### Revenue Domain
- **Sales Orders:** Raw POS data from Petpooja → `sales_raw_layer`
- **Sales Items:** Parsed line items → `sales_items_parsed`
- **Sales Enhanced:** Enriched with customer/delivery metadata → `sales_enhanced`

### Expense Domain
- **Expenses:** Category-based tracking → `expenses_master`
- **Cash Flow:** Withdrawals/topups → `cash_flow_master`
- **Purchases:** Ingredient procurement → `purchases_master`

### Inventory Domain
- **Ingredients:** Raw materials → `ingredients_master`
- **Recipes (Sales):** Item composition → `recipes_sales_master`
- **Recipes (Production):** Sub-recipe assembly → `recipes_production_master`
- **Wastage:** Loss tracking → `wastage_log`

### System Domain
- **Evolution Log:** Self-improvement tracking → `dev_evolution_log`
- **Error Log:** System errors → `system_error_log`
- **Sync Log:** ETL status → `system_sync_log`
- **Cost Log:** BigQuery spend → `system_cost_log`

---

## 🔄 Key Data Flows

### 1. Sales Sync Flow
```
Petpooja POS API 
  → sync_sales_raw.py (Secondary Adapter)
  → sales_raw_layer (BigQuery)
  → enhanced_sales_parser.py (Transform)
  → sales_enhanced (BigQuery)
  → Dashboard/API (Primary Adapter)
```

### 2. Expense Sync Flow
```
Google Drive Excel Files
  → sync_expenses.py (Secondary Adapter)
  → expenses_master (BigQuery)
  → Expense Analysis Engine (Domain Logic)
  → Dashboard Charts (Primary Adapter)
```

### 3. Chat Intelligence Flow
```
User Query (Next.js/Streamlit)
  → /chat/stream API endpoint
  → gemini_chat.py (Application Service)
  → BigQuery Context Retrieval
  → Gemini AI API (Secondary Adapter)
  → Streaming Response (Primary Adapter)
```

---

## 🧪 Adapter Definitions

### Primary Adapters (Driving/Inbound)
| Adapter | Technology | Port Interface |
|---------|-----------|----------------|
| REST API | FastAPI | `/health`, `/chat`, `/metrics`, `/ops` |
| Web UI | Next.js 16 + React 19 | Pages: dashboard, chat, operations, settings |
| Admin Dashboard | Streamlit | `titan_app.py` (legacy, being phased out) |

### Secondary Adapters (Driven/Outbound)
| Adapter | External System | Integration Method |
|---------|----------------|-------------------|
| BigQuery Adapter | Google BigQuery | `google-cloud-bigquery` SDK |
| Drive Adapter | Google Drive | `google-api-python-client` |
| POS Adapter | Petpooja API | REST API (custom HTTP client) |
| AI Adapter | Gemini API | HTTP requests to `generativelanguage.googleapis.com` |

---

## 🎯 Petpooja Integration Points

### Endpoints Consumed
1. **Sales Data:** Fetch order history with full JSON payload
2. **Inventory:** Real-time stock levels (future)
3. **Menu Items:** Item catalog sync (future)

### Data Mapping
- **Order Status:** Normalized to exclude "cancel" variants
- **Revenue:** Multi-path extraction (`order_total`, `total`, `grand_total`)
- **Delivery Partner:** Extracted from JSON payload when column missing

---

## 📈 Evolution & Self-Development

The system tracks its own improvements in `dev_evolution_log`:
- **Feature additions** suggested by AI
- **Bug fixes** identified by Sentinel Hub
- **Performance optimizations** logged by guardrails
- **User feedback** captured via Chat Intelligence

---

## 🚨 Health Monitoring

### Sentinel Hub (`04_Intelligence_Lab/sentinel_hub.py`)
Monitors:
- Revenue anomalies (>10% deviation)
- Data freshness (stale sync warnings)
- Expense spikes
- Missing data gaps

### Cost Guardrails (`utils/bq_guardrails.py`)
- Dry-run cost estimation before query execution
- Monthly budget tracking (₹1000 default)
- Query-level cost logging
- Budget breach prevention

---

## 🔮 Future Roadmap (Per TITAN_DNA.json)

1. **Multi-Tenant Isolation:** Row-level security in BigQuery
2. **Recipe Intelligence:** Auto-detect ingredient usage anomalies
3. **Predictive Analytics:** Demand forecasting via ML
4. **Mobile App:** React Native companion
5. **Webhook Integration:** Real-time Petpooja events

---

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}  
**Maintained By:** TITAN Self-Evolution Engine  
**Questions?** Check `TITAN_VISION.md` or ask via Intelligence Chat
