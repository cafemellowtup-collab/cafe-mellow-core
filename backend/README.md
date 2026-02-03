# TITAN ERP - Backend Architecture

**Version:** 6.5.0 - God Mode Complete  
**Status:** Production-Ready  
**Last Updated:** February 1, 2026

---

## Overview

The TITAN backend is an AI-powered data intelligence platform built with FastAPI, BigQuery, and Google Gemini. It provides:

- **Universal Data Ingestion** - Accept any Excel/CSV file, auto-detect structure
- **Semantic Classification** - AI categorizes events with confidence scoring
- **Natural Language Queries** - Ask questions in plain English, get SQL + answers
- **Adaptive AI Personality** - Cortex adapts to user data maturity
- **God Mode Control** - Master controls features and AI behavior without code

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TITAN BACKEND                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   INGEST    │    │   BRAIN     │    │   CORTEX    │    │   MASTER    │  │
│  │             │───>│             │───>│             │<───│             │  │
│  │ Universal   │    │ Semantic    │    │ Adaptive    │    │ God Mode    │  │
│  │ Adapter     │    │ Brain       │    │ Personality │    │ Control     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         v                  v                  v                  v          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      UNIVERSAL LEDGER (BigQuery)                     │   │
│  │                     Immutable Event Storage                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

```
Raw File → Structure Detective → Column Mapper → Semantic Brain → Ledger Writer
                                                       ↓
                                               [Confidence Check]
                                                ↓            ↓
                                            ≥85%          <85%
                                               ↓            ↓
                                        Main Ledger    Quarantine
                                                           ↓
                                                    Human Review
                                                           ↓
                                                    Brain Learns
```

---

## 🏰 Phase 8 - Fortress Upgrade (Ingestion Hardening)

- **Bouncer:** Schema validation rejects junk/unknown files before processing.
- **Sherlock:** Strict STREAM (Sales) vs STATE (Menu) classification using filename + column hints.
- **Turbo Engine:** Async batch classification in chunks of 50 for large uploads.
- **Ghost Logic:** Auto-creates provisional menu items for unknown sales entities; STATE uploads convert provisional → official.

---

## Core Components

### 1. Universal Adapter (Ingestion Layer)

**Purpose:** Accept any file format, detect structure, transform to events.

**Key Files:**
- `universal_adapter/structure_detective.py` - Header detection (Golden Path + Deep Scan)
- `universal_adapter/column_mapper.py` - Fuzzy column matching
- `universal_adapter/semantic_brain.py` - AI classification
- `universal_adapter/ledger_writer.py` - BigQuery persistence

**Endpoint:** `POST /api/v1/ingest/file`

---

### 2. Semantic Brain (Classification Engine)

**Purpose:** Categorize events using Gemini AI with learning capability.

**Features:**
- 15+ event categories (SALES, INVENTORY, EXPENSE, etc.)
- Confidence scoring (0-100%)
- Pattern caching (learns from corrections)
- Batch classification

**Key File:** `universal_adapter/semantic_brain.py`

---

### 3. Titan Cortex (The Personality)

**Purpose:** Adaptive AI personality that matches user data maturity.

**Persona Adaptation:**
| Data State | AI Persona |
|------------|------------|
| Empty | Friendly Onboarding Guide |
| Sparse | Patient Mentor |
| Growing | Engaged Analyst |
| Mature | Strategic CFO |

**Features:**
- Deep history analysis
- Simulation mode ("What if?" questions)
- User preference handling (currency, fiscal year, exclusions)
- Global rules injection from Master

**Key File:** `universal_adapter/titan_cortex.py`

**The Link:** Cortex reads `MasterConfig` and injects feature restrictions into prompts. If Master disables "simulation_mode" for a tenant, Cortex tells the AI to politely decline.

---

### 4. Query Engine (Natural Language to SQL)

**Purpose:** Convert plain English questions to BigQuery SQL and human-readable answers.

**Flow:**
```
User Question → Cortex builds context → Gemini generates SQL → Execute → Format Answer
```

**Example:**
- Input: "What were my sales last week?"
- SQL: `SELECT SUM(amount) FROM universal_ledger WHERE tenant_id='...' AND category='SALES' AND timestamp >= '...'`
- Answer: "Your sales last week totaled ₹45,230 across 127 transactions."

**Key File:** `universal_adapter/query_engine.py`

**Endpoint:** `POST /api/v1/query/ask`

---

### 5. Master API (God Mode Control)

**Purpose:** Central control panel for the Master to manage all tenants without code.

**Authentication:** `X-Master-Key` header (set via `MASTER_KEY` env var)

**Capabilities:**
- Enable/disable features per tenant
- Inject global AI behavior rules
- View system evolution suggestions
- Read friction logs

**Key Files:**
- `core/master_config.py` - Tenant config and rules manager
- `api/routers/master.py` - God Mode endpoints

**Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/master/god/tenant/feature` | POST | Enable/disable feature |
| `/api/v1/master/god/tenant/{id}/config` | GET | Get tenant config |
| `/api/v1/master/god/brain/rule` | POST | Add global AI rule |
| `/api/v1/master/god/brain/rules` | GET | List all rules |
| `/api/v1/master/god/evolution/suggestions` | GET | Get feature suggestions |

**Example - Disable Simulation Mode:**
```bash
curl -X POST "http://localhost:8000/api/v1/master/god/tenant/feature" \
  -H "X-Master-Key: your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "tenant-x", "feature": "simulation_mode", "enabled": false}'
```

**Result:** When tenant-x asks "What if I sell 5kg?", AI responds: "Simulation mode is not available on your current plan."

---

### 6. System Evolution (Self-Improvement)

**Purpose:** Track friction points and suggest features to the creator.

**Features:**
- Friction logging (when users hit walls)
- Pattern detection (common struggles)
- AI-powered feature suggestions
- Creator feedback loop

**Key File:** `core/system_evolution.py`

**Endpoint:** `GET /api/v1/master/god/evolution/suggestions`

---

## Directory Structure

```
backend/
├── core/
│   ├── master_config.py        # God Mode configuration
│   ├── system_evolution.py     # Friction tracking & suggestions
│   └── titan_v3/               # TITAN AI engine
│       ├── unified_engine.py
│       ├── active_senses.py
│       └── knowledge_graph.py
│
├── universal_adapter/
│   ├── titan_cortex.py         # Adaptive AI personality
│   ├── query_engine.py         # NL → SQL → Answer
│   ├── semantic_brain.py       # AI classification
│   ├── structure_detective.py  # Header detection
│   ├── column_mapper.py        # Fuzzy matching
│   └── ledger_writer.py        # BigQuery writer
│
├── tools/
│   └── factory_reset.py        # The Nuke Button
│
└── pillars/
    └── config_vault.py         # Centralized configuration
```

---

## Data Files

Located in `data/` directory:

| File | Purpose | Preserved on Reset? |
|------|---------|---------------------|
| `universal_ledger.jsonl` | Local event storage (fallback) | ❌ Deleted |
| `brain_cache.json` | Learned semantic mappings | ✅ Kept |
| `tenant_configs.json` | Per-tenant feature flags | ❌ Deleted |
| `global_rules.json` | Master's AI rules | ✅ Kept |
| `system_evolution_log.json` | Friction points log | ❌ Deleted |
| `user_preferences.json` | User settings | ❌ Deleted |

---

## Environment Variables

```env
# Required
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-gcp-project

# Optional
MASTER_KEY=your-master-key-for-god-mode
BQ_DATASET=cafe_operations
BQ_TABLE_LEDGER=universal_ledger
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your keys

# 3. Run the server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 4. Test health
curl http://localhost:8000/health
```

---

## API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Tools

### Factory Reset

Clear test data while preserving intelligence:

```bash
python backend/tools/factory_reset.py
```

Options:
- `--force` - Skip confirmation
- `--status` - Show status only
- `--quick` - Quiet mode for scripts

---

## Testing

```bash
# Phase 6 tests (God Mode)
python tests/quick_test_phase6.py

# Ingestion tests
python tests/verify_ingest_endpoint.py

# Full test suite
pytest tests/
```

---

## Related Documentation

- `VISION.md` - System philosophy and manifesto
- `PROJECT_ROADMAP.md` - Complete roadmap and progress
- `universal_adapter/README.md` - Detailed ingestion documentation

---

**Built with 🔥 by TITAN Evolution Engine**
