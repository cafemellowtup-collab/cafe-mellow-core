# 🏗️ TITAN ERP - Complete System Architecture

**Version 4.0 - Universal Semantic Brain Edition** | January 2026

---

## 📊 System Overview

TITAN is a **production-grade AI-powered ERP** with three revolutionary capabilities:

1. **Universal Semantic Brain** - AI that understands ANY data without predefined rules
2. **Immutable Event Ledger** - Every data change is tracked and auditable
3. **Multi-Tenant SaaS Architecture** - Scales to 1 Lakh+ subscribers

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TITAN ERP ARCHITECTURE                              │
│                         "Intelligence for Every Decision"                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND LAYER (Next.js 16 + React 19)                                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│  │  Chat AI   │ │ Dashboard  │ │ Operations │ │ Quarantine │ │  Settings  │    │
│  │ (TITAN CFO)│ │  (KPIs)    │ │ (Expenses) │ │  (Review)  │ │ (Config)   │    │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Components: AppShell, NotificationCenter, VoiceInput, PDFExport       │    │
│  │  Contexts: AuthContext, TenantContext, RBACContext                      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ HTTPS/REST
┌─────────────────────────────────────────────────────────────────────────────────┐
│  API LAYER (FastAPI on Cloud Run)                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Routers:                                                               │    │
│  │  ├── /api/v1/brain/*      - Universal Semantic Brain (NEW)              │    │
│  │  ├── /api/v1/adapter/*    - Universal Adapter (Airlock, Guard, etc.)    │    │
│  │  ├── /api/v1/chat/*       - AI Chat Intelligence                        │    │
│  │  ├── /api/v1/analytics/*  - Dashboard Analytics                         │    │
│  │  ├── /api/v1/auth/*       - Authentication (JWT)                        │    │
│  │  ├── /api/v1/users/*      - User Management                             │    │
│  │  ├── /api/v1/sync/*       - Data Sync Operations                        │    │
│  │  ├── /api/v1/oracle/*     - AI Oracle (Natural Language Queries)        │    │
│  │  └── /api/v1/webhook/*    - External Webhook Ingestion                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  INTELLIGENCE LAYER (Python Backend)                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Universal Semantic Brain:                                              │    │
│  │  ├── semantic_brain.py     - AI auto-classification (15+ categories)   │    │
│  │  ├── polymorphic_ledger.py - Universal event storage                   │    │
│  │  ├── universal_ingestion.py - Pipeline connecting all components       │    │
│  │  └── event_ledger.py       - Immutable audit trail                     │    │
│  │                                                                         │    │
│  │  Universal Adapter:                                                     │    │
│  │  ├── airlock.py            - Never-crash ingestion layer               │    │
│  │  ├── refinery.py           - Data transformation                       │    │
│  │  ├── golden_schema.py      - Target schemas                            │    │
│  │  ├── guard.py              - Validation + write to main DB             │    │
│  │  ├── processor.py          - Background batch processing               │    │
│  │  └── reconciliation.py     - Data quality monitoring                   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Pillars (Domain Logic):                                                │    │
│  │  ├── chat_intel.py         - AI conversation memory                    │    │
│  │  ├── dashboard.py          - Revenue/expense analytics                 │    │
│  │  ├── config_vault.py       - Configuration management                  │    │
│  │  ├── users_roles.py        - RBAC implementation                       │    │
│  │  └── evolution.py          - Self-improvement tracking                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DATA LAYER (Google BigQuery)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Tables (cafe_operations dataset):                                      │    │
│  │  ├── universal_events     - Polymorphic event ledger (ALL data)         │    │
│  │  ├── event_log            - Immutable audit trail                       │    │
│  │  ├── sales_raw            - POS sales transactions                      │    │
│  │  ├── expenses             - Expense records                             │    │
│  │  ├── purchases            - Purchase orders                             │    │
│  │  ├── raw_logs             - Ingestion staging table                     │    │
│  │  ├── quarantine           - Failed records for review                   │    │
│  │  ├── schema_mappings      - Source-to-target mappings                   │    │
│  │  ├── category_registry    - Semantic categories                         │    │
│  │  └── auth_users           - User authentication                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AI LAYER (Google Gemini 2.0 Flash)                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Capabilities:                                                          │    │
│  │  ├── Semantic Classification  - Understands ANY data                    │    │
│  │  ├── Natural Language Query   - SQL generation from English            │    │
│  │  ├── Anomaly Detection        - Finds profit leaks automatically       │    │
│  │  ├── Task Generation          - Creates [TASK:] action items           │    │
│  │  └── Daily Briefs             - Executive summaries                    │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Universal Semantic Brain

The breakthrough AGI-for-data-engineering system that classifies ANY data:

### How It Works

```
ANY INPUT DATA                    SEMANTIC BRAIN                    OUTPUT
───────────────────────────────────────────────────────────────────────────
{"orderID": "123",      ──►    Pattern Matching     ──►    category: "sales"
 "total": 500,                      +                      sub_cat: "dine_in"
 "customer": "John"}          Gemini AI Analysis          confidence: 0.92
                                    │
                                    ▼
                              ┌───────────┐
                              │ confidence│
                              │  > 85%?   │
                              └─────┬─────┘
                           YES      │      NO
                            ▼       │       ▼
                      AUTO-STORE    │   HUMAN REVIEW
                      (verified)    │   (quarantine)
```

### Supported Business Concepts (15+)

| Category | Detection Keywords | Example |
|----------|-------------------|---------|
| SALES | order, invoice, payment, customer | POS transactions |
| EXPENSE | vendor, cost, salary, utility | Operational costs |
| INVENTORY | stock, ingredient, quantity | Raw materials |
| RECIPE | ingredients, preparation, cooking | Product recipes |
| MENU | menu, dish, price, category | Menu items |
| CRM | customer, guest, contact | Customer profiles |
| STAFF | employee, role, salary | HR records |
| VENDOR | supplier, gst, credit | Supplier data |
| FEEDBACK | review, rating, complaint | Customer reviews |
| RESERVATION | booking, table, party | Table bookings |
| LOYALTY | points, rewards, tier | Loyalty programs |
| MARKETING | campaign, promotion, coupon | Marketing data |
| FINANCE | ledger, tax, audit | Accounting records |
| OPERATIONS | shift, schedule, task | Operational data |
| INFRASTRUCTURE | equipment, sensor, energy | IoT/equipment data |

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AUTHENTICATION FLOW                                                            │
│                                                                                 │
│  User ──► Login Page ──► /api/v1/auth/login ──► JWT Token ──► Protected Routes │
│                                │                                                │
│                                ▼                                                │
│                         BigQuery: auth_users                                    │
│                         (password: SHA256 + salt)                               │
│                                                                                 │
│  Token Expiry: 7 days                                                           │
│  Storage: localStorage (titan.auth.token)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  MULTI-TENANT ISOLATION                                                         │
│                                                                                 │
│  Every table has: tenant_id (STRING, NOT NULL)                                  │
│                                                                                 │
│  Tenant A data ◄────────────────────────► Tenant B data                         │
│       │                                         │                               │
│       └─────────── COMPLETELY ISOLATED ─────────┘                               │
│                                                                                 │
│  BigQuery Row-Level Security + Application-Level Filtering                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
Cafe_AI/
├── api/                           # FastAPI REST Layer
│   ├── main.py                    # App initialization, router registration
│   └── routers/                   # API endpoints
│       ├── semantic_brain.py      # Universal Semantic Brain API
│       ├── universal_adapter.py   # Data ingestion/quarantine
│       ├── chat.py                # AI chat endpoints
│       ├── auth.py                # Authentication
│       ├── analytics.py           # Dashboard analytics
│       ├── oracle.py              # Natural language queries
│       └── ...                    # Other routers
│
├── backend/                       # Business Logic Layer
│   ├── universal_adapter/         # Data ingestion system
│   │   ├── semantic_brain.py      # AI classification engine
│   │   ├── polymorphic_ledger.py  # Universal event storage
│   │   ├── universal_ingestion.py # Integration pipeline
│   │   ├── airlock.py             # Never-crash ingestion
│   │   ├── event_ledger.py        # Immutable audit log
│   │   ├── guard.py               # Validation layer
│   │   ├── refinery.py            # Data transformation
│   │   ├── processor.py           # Background processing
│   │   └── init_tables.py         # BigQuery table setup
│   │
│   └── core/                      # Core domain logic
│       ├── enhanced_chat.py       # Streaming AI chat
│       ├── petpooja_adapter.py    # POS integration
│       └── ...
│
├── pillars/                       # Domain Services
│   ├── chat_intel.py              # Chat memory/intelligence
│   ├── dashboard.py               # Analytics computations
│   ├── config_vault.py            # Configuration management
│   └── users_roles.py             # RBAC
│
├── utils/                         # Utilities
│   ├── bq_guardrails.py           # BigQuery cost protection
│   ├── gemini_chat.py             # Gemini AI wrapper
│   ├── ops_brief.py               # Daily brief generation
│   └── ai_task_queue.py           # Task automation
│
├── web/                           # Next.js Frontend
│   └── src/
│       ├── app/
│       │   ├── (auth)/            # Login/Signup pages
│       │   ├── (dashboard)/       # Protected pages
│       │   │   ├── chat/          # AI Chat
│       │   │   ├── dashboard/     # KPI Dashboard
│       │   │   ├── operations/    # Expense management
│       │   │   └── settings/      # Configuration
│       │   └── (public)/          # Landing page
│       │
│       ├── components/            # Reusable components
│       │   ├── AppShell.tsx       # Main layout with nav
│       │   ├── NotificationCenter.tsx
│       │   ├── VoiceInput.tsx
│       │   └── ...
│       │
│       └── contexts/              # React contexts
│           ├── AuthContext.tsx    # Authentication state
│           ├── TenantContext.tsx  # Multi-tenant context
│           └── RBACContext.tsx    # Role-based access
│
├── 01_Data_Sync/                  # ETL Scripts
│   ├── sync_sales_raw.py          # POS sync
│   ├── sync_expenses.py           # Google Drive sync
│   └── ...
│
└── docs/                          # Documentation
    └── architecture/              # Architecture diagrams
```

---

## 🚀 API Endpoints Reference

### Universal Semantic Brain (`/api/v1/brain`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/classify` | Classify any data |
| POST | `/ingest` | Universal ingestion |
| POST | `/ingest/batch` | Batch ingestion |
| GET | `/categories` | List all categories |
| GET | `/events` | Query stored events |
| GET | `/summary` | 360° business summary |
| GET | `/pending-reviews` | Human review queue |
| POST | `/verify` | Verify/correct event |

### Universal Adapter (`/api/v1/adapter`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/schemas` | List golden schemas |
| GET | `/quarantine` | List quarantined records |
| POST | `/quarantine/{id}/approve` | Approve record |
| POST | `/quarantine/{id}/reject` | Reject record |
| GET | `/stats` | Processing statistics |

### Webhook Ingestion (`/api/v1/webhook`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/{source}` | Ingest from any source |
| POST | `/ingest/petpooja` | Petpooja POS webhook |
| POST | `/bulk` | Bulk data ingestion |

### Chat (`/api/v1/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/message` | Send chat message |
| GET | `/context` | Get chat context |
| GET | `/history` | Get chat history |

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | User login (returns JWT) |
| POST | `/signup` | User registration |
| GET | `/verify` | Verify JWT token |
| POST | `/logout` | Logout user |

---

## 🔧 Environment Variables

```bash
# Google Cloud
PROJECT_ID=cafe-mellow-core-2026
DATASET_ID=cafe_operations
GOOGLE_APPLICATION_CREDENTIALS=service-key.json

# AI
GEMINI_API_KEY=your_gemini_api_key

# Petpooja POS
PP_APP_KEY=your_petpooja_app_key
PP_APP_SECRET=your_petpooja_secret
PP_ACCESS_TOKEN=your_access_token
PP_MAPPING_CODE=your_mapping_code

# Google Drive Folders
FOLDER_ID_EXPENSES=your_folder_id
FOLDER_ID_PURCHASES=your_folder_id
FOLDER_ID_INVENTORY=your_folder_id

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://cafe-mellow-backend-564285438043.asia-south1.run.app
```

---

## 📈 Scaling Capabilities

| Metric | Capacity | Technology |
|--------|----------|------------|
| Users | 1 Lakh+ | Multi-tenant isolation |
| Events/day | 10 Million+ | BigQuery streaming |
| API requests | Unlimited | Cloud Run auto-scaling |
| Data scenarios | 2 Crore+ | AI pattern learning |
| Storage | Petabytes | BigQuery |

---

## 🔗 Production URLs

- **Backend API**: https://cafe-mellow-backend-564285438043.asia-south1.run.app
- **Frontend**: https://cafe-mellow-core.vercel.app
- **API Docs**: https://cafe-mellow-backend-564285438043.asia-south1.run.app/docs

---

*Last Updated: January 27, 2026*
