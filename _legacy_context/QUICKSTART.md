# 🚀 GENESIS PROTOCOL - Quick Start Guide

## Prerequisites

- Python 3.10+
- Google Cloud Project with BigQuery enabled
- Service account JSON key file (`service-key.json`)
- Gemini API key

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and fill in your values
# Minimum required:
# - GEMINI_API_KEY
# - CRON_SECRET (generate: openssl rand -hex 32)
```

## Step 3: Setup BigQuery Tables

```bash
python scripts/setup_genesis.py
```

This creates:
- `users` - User accounts with RBAC
- `roles` - Role definitions
- `entities` - Employees/Vendors
- `ledger_universal` - Universal financial ledger
- `data_quality_scores` - Data quality tracking
- `system_knowledge_base` - AI documentation
- `learned_strategies` - AI-learned business rules
- `user_activity_log` - Audit trail

## Step 4: (Optional) Migrate Existing Data

```bash
python scripts/migrate_to_ledger.py
```

Follow prompts to enter your `org_id` and `location_id`.

## Step 5: Start the API

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Step 6: Test the System

### Check API Health
```bash
curl http://localhost:8000/health
```

### Test Data Quality Score
```bash
curl "http://localhost:8000/analytics/data_quality?org_id=test&location_id=test&days=30"
```

### Test Adaptive Profit Calculation
```bash
curl "http://localhost:8000/analytics/profit?org_id=test&location_id=test&start_date=2026-01-01&end_date=2026-01-31"
```

## Architecture Overview

```
backend/
├── core/                    # Domain Logic (Framework Agnostic)
│   ├── security/           # RBAC, Entities, Tenant Isolation
│   ├── ledger/             # Universal Ledger
│   ├── events/             # Event Bus (Observer Pattern)
│   ├── chameleon/          # Adaptive Intelligence
│   ├── metacognitive/      # AI Self-Evolution
│   └── compliance/         # DPDP Export
├── adapters/               # External Integrations
│   └── storage/            # Cloudflare R2
└── schemas/                # BigQuery DDL

api/
└── routers/                # Modular API Endpoints
    ├── cron.py             # Serverless Automation
    ├── ledger.py           # Financial Transactions
    ├── analytics.py        # Business Intelligence
    └── hr.py               # Human Resources
```

## Key Features

### 1. **CITADEL (Security)**
- RBAC with scoped permissions
- Entities (Employees/Vendors) separate from Users
- Tenant isolation (org_id + location_id)

### 2. **UNIVERSAL LEDGER**
- Single source of truth for all financial events
- Types: SALE, EXPENSE, WASTAGE, TOPUP, LOAN, DIVIDEND, SALARY_ADVANCE
- Flexible JSON metadata

### 3. **CHAMELEON BRAIN**
- Data quality scoring (0-100)
- Adaptive strategies:
  - RED (< 50): Estimation
  - YELLOW (50-90): Hybrid
  - GREEN (> 90): Audit-grade

### 4. **EVENT BUS**
- Decoupled architecture
- No function chaining
- Observer pattern

### 5. **CRON AUTOMATION**
- Serverless (Cloud Scheduler compatible)
- Secured with CRON_SECRET
- Jobs: daily_close, run_payroll, sync_sales

## Next Steps

1. **Configure Cloud Scheduler** (see `GENESIS_PROTOCOL.md`)
2. **Setup R2 Storage** (optional, for file uploads)
3. **Migrate existing data** (gradual, Strangler Fig pattern)
4. **Deploy to Cloud Run** (production)

## Documentation

- **Full Guide:** `GENESIS_PROTOCOL.md`
- **API Docs:** http://localhost:8000/docs
- **Architecture:** `BLUEPRINT.md`
- **Vision:** `TITAN_VISION.md`

## Troubleshooting

### "CRON_SECRET not configured"
Set in `.env`: `CRON_SECRET=your_secret_here`

### "R2 credentials not configured"
Optional unless using file uploads. Set R2_* variables in `.env`

### "Table not found"
Run: `python scripts/setup_genesis.py`

### Import errors
Run: `pip install -r requirements.txt`

## Support

Check `GENESIS_PROTOCOL.md` for detailed documentation.
