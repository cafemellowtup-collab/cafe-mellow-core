# Universal Adapter - Event-Driven AI Platform

> **The Funnel of Truth**: Wide at the top (accepts anything), narrow at the bottom (only perfect data enters).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL ADAPTER ARCHITECTURE                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   [ANY SOURCE]  ──►  [AIRLOCK]  ──►  [RAW_LOGS]                 │
│   - Petpooja         POST /api/     BigQuery                    │
│   - Excel            webhook/       table                        │
│   - Zoho             ingest                                      │
│   - Future APIs                                                  │
│                          │                                       │
│                          ▼                                       │
│                   [AI REFINERY]                                  │
│                   Background Worker                              │
│                   - Classify source                              │
│                   - Check mapping cache                          │
│                   - AI transform if needed                       │
│                          │                                       │
│                          ▼                                       │
│                   [GUARD/VALIDATOR]                              │
│                   Pydantic + Golden Schema                       │
│                          │                                       │
│              ┌──────────┴──────────┐                            │
│              ▼                     ▼                             │
│         [PASS]                [FAIL]                             │
│         Main DB               Quarantine UI                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Golden Schema (`backend/universal_adapter/golden_schema.py`)
Pydantic models defining the "law" of valid data:
- `GoldenOrder` - Sales orders with items, payments, discounts
- `GoldenExpense` - Business expenses with categorization
- `GoldenPurchase` - Inventory purchases from vendors

### 2. Airlock (`backend/universal_adapter/airlock.py`)
**Indestructible ingestion layer** - NEVER crashes, accepts ANY payload.
- Saves raw data to `raw_logs` table immediately
- Returns success instantly
- Background worker processes later

### 3. AI Refinery (`backend/universal_adapter/refinery.py`)
Intelligent transformation engine:
- Uses cached mappings for known sources (fast path)
- Uses Gemini AI for unknown sources (slow path, but learns)
- Optimized Petpooja transformer with hardcoded mappings

### 4. Guard (`backend/universal_adapter/guard.py`)
Validation and quarantine system:
- Final validation against Golden Schema
- PASS → Write to main BigQuery tables
- FAIL → Write to quarantine for human review

### 5. Processor (`backend/universal_adapter/processor.py`)
Background worker that processes the queue:
- Single record processing
- Batch processing
- Retry failed records

---

## API Endpoints

### Ingestion (Airlock)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/webhook/ingest` | POST | Generic catch-all for any data |
| `/api/v1/webhook/ingest/{source_type}` | POST | Source-specific ingestion |
| `/api/v1/webhook/ingest/file` | POST | File upload (Excel, CSV) |
| `/api/v1/webhook/status/{log_id}` | GET | Check processing status |
| `/api/v1/webhook/pending` | GET | List pending records |
| `/api/v1/webhook/stats` | GET | Ingestion statistics |

### Transformation & Processing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/adapter/health` | GET | Health check |
| `/api/v1/adapter/schemas` | GET | List available schemas |
| `/api/v1/adapter/schemas/{name}` | GET | Get schema JSON |
| `/api/v1/adapter/transform` | POST | Manual transformation test |
| `/api/v1/adapter/transform/petpooja` | POST | Petpooja-specific transform |
| `/api/v1/adapter/process/single/{log_id}` | POST | Process single record |
| `/api/v1/adapter/process/batch` | POST | Process batch of pending |
| `/api/v1/adapter/process/retry` | POST | Retry failed records |

### Quarantine Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/adapter/quarantine` | GET | List quarantined records |
| `/api/v1/adapter/quarantine/stats` | GET | Quarantine statistics |
| `/api/v1/adapter/quarantine/approve` | POST | Approve with corrections |
| `/api/v1/adapter/quarantine/reject` | POST | Reject record |

---

## Usage Examples

### 1. Ingest Petpooja Order
```bash
curl -X POST https://cafe-mellow-backend-564285438043.asia-south1.run.app/api/v1/webhook/ingest/petpooja \
  -H "Content-Type: application/json" \
  -d '{
    "Order": {
      "orderID": "ORD001",
      "order_date": "2025-01-27",
      "order_total": 1500,
      "customer_name": "John Doe"
    },
    "OrderItem": [
      {"name": "Coffee", "quantity": 2, "price": 300},
      {"name": "Sandwich", "quantity": 1, "price": 200}
    ]
  }'
```

Response:
```json
{
  "ok": true,
  "message": "Data received for petpooja",
  "log_id": "log_petpooja_20260127...",
  "status": "pending"
}
```

### 2. Process the Record
```bash
curl -X POST https://cafe-mellow-backend-564285438043.asia-south1.run.app/api/v1/adapter/process/single/log_petpooja_20260127...
```

Response:
```json
{
  "ok": true,
  "log_id": "log_petpooja_20260127...",
  "status": "completed",
  "target_schema": "order"
}
```

### 3. Check Status
```bash
curl https://cafe-mellow-backend-564285438043.asia-south1.run.app/api/v1/webhook/status/log_petpooja_20260127...
```

### 4. Upload Excel File
```bash
curl -X POST https://cafe-mellow-backend-564285438043.asia-south1.run.app/api/v1/webhook/ingest/file \
  -F "file=@expenses.xlsx" \
  -F "source_type=expense"
```

---

## BigQuery Tables

| Table | Description |
|-------|-------------|
| `raw_logs` | All ingested raw data (audit trail) |
| `quarantine` | Failed records awaiting review |
| `schema_mappings` | Cached field mappings (learning) |
| `sales_orders_enhanced` | Validated orders |
| `sales_order_items_enhanced` | Order line items |
| `sales_order_payments` | Payment records |
| `sales_order_discounts` | Discount records |
| `expenses` | Validated expenses |
| `purchases` | Validated purchases |

---

## Initialize Tables
```bash
cd /path/to/Cafe_AI
$env:PYTHONPATH = "."
python backend/universal_adapter/init_tables.py
```

---

## Key Features

1. **Never Crashes** - Airlock accepts ANY payload, even malformed JSON
2. **AI-Powered Mapping** - Gemini AI figures out field mappings for unknown sources
3. **Learning System** - Caches successful mappings for future use
4. **Human-in-the-Loop** - Failed records go to quarantine for review
5. **Audit Trail** - Raw data preserved in `raw_logs` forever
6. **Optimized Paths** - Known sources (Petpooja) use hardcoded fast transformers

---

## 🏰 Phase 8 - Fortress Upgrade

1. **The Bouncer (Schema Validation)**
   - Rejects junk/unknown files before processing.
   - Requires critical columns: Date+Amount (STREAM) or Item+Price (STATE).
2. **The Sherlock (Strict Classification)**
   - Deterministic STREAM vs STATE classification using filename + column hints.
   - Falls back to column signals when filename hints are weak.
3. **Turbo Engine (Async Batches)**
   - Classifies large uploads in async chunks of 50 to avoid timeouts.
4. **Ghost Logic (Resilience)**
   - STREAM: auto-creates provisional menu items for unknown sales entities.
   - STATE: upserts items and converts provisional → official.

---

## Production URLs

- **Backend**: https://cafe-mellow-backend-564285438043.asia-south1.run.app
- **Health Check**: https://cafe-mellow-backend-564285438043.asia-south1.run.app/api/v1/adapter/health
