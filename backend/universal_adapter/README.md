# 🔌 Module: Universal Adapter (Ingestion Layer)

**Version:** 2.0.0  
**Status:** ✅ Production-Ready (Verified Jan 31, 2026)  
**Maintainer:** TITAN Evolution Engine

---

## Purpose

The **"Magic Door"** for TITAN. Accepts raw tabular data (CSV/Excel) from ANY source, cleans it, and prepares it for the Universal Ledger.

This module enables:
- **Source-Agnostic Ingestion:** PetPooja, Tally, QuickBooks, custom spreadsheets - all welcome
- **Zero-Configuration Parsing:** Auto-detects file type and structure
- **Multi-Tenant Isolation:** Each tenant's data stays isolated via `X-Tenant-ID` header
- **Safe Processing:** Converts all data to JSON before downstream processing

---

## 📂 Architecture

```
backend/universal_adapter/
├── README.md              # This file (Module Passport)
├── structure_detective.py # 🔍 Header detection (Golden Path + Deep Scan)
├── mapper.py              # 🗺️ Fuzzy column matching to Universal Events
├── polymorphic_ledger.py  # Universal event storage schema
├── semantic_brain.py      # AI classification engine
├── event_ledger.py        # Event logging utilities
├── reconciliation.py      # Data reconciliation logic
└── airlock.py             # Raw JSON catch-all endpoint

api/routers/
├── ingest.py              # ⭐ Entry Point - File upload endpoint
├── universal_adapter.py   # Universal event management
└── semantic_brain.py      # Classification API
```

### Data Flow Pipeline
```
┌─────────────┐     ┌─────────────────────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────────┐
│  Raw File   │ --> │  Structure Detective    │ --> │ Clean DF │ --> │   Mapper    │ --> │ Universal Events │
│ (xlsx/csv)  │     │  (w/ AI Judge Fallback) │     │          │     │ (Fuzzy Col) │     │                  │
└─────────────┘     └─────────────────────────┘     └──────────┘     └─────────────┘     └──────────────────┘
```

### Entry Point
**`api/routers/ingest.py`** - The primary file upload handler

### Supported Formats
| Format | Extension | Engine |
|--------|-----------|--------|
| Excel 2007+ | `.xlsx` | pandas + openpyxl |
| Legacy Excel | `.xls` | pandas + openpyxl |
| CSV | `.csv` | pandas |

### Rejected Formats (Returns 400)
- `.pdf` - Not yet supported
- `.txt` - Not tabular data
- `.png`, `.jpg`, `.gif` - Image files
- `.exe`, `.bat` - Unsafe executables

---

## 🧠 The Intelligence Layer

### Structure Detective (`structure_detective.py`)

Automatically finds the **real header row** in messy files (skips logos, titles, blank rows).

| Mode | Trigger | Description |
|------|---------|-------------|
| **Golden Path** | Row 0/1 has ≥3 keywords | Instant return, no scanning. Protects simple files. |
| **Deep Scan** | Golden Path fails | Scans up to **500 rows** for buried headers. |
| **AI Judge** | Two candidates within 2 points | Uses **Gemini Flash** to disambiguate multi-table files. |

**Scoring System:**
- Base Score: Count of anchor keywords (`date`, `amount`, `item`, `total`, etc.)
- Bonus +2: Contains BOTH `date` AND `amount/total` (Transactional Indicator)
- Bonus +1: Row below contains numeric data (Data Check)

**Example:** A "Summary Table" at Row 5 scores 4 points. A "Detail Ledger" at Row 200 scores 9 points. The Detective picks Row 200.

---

### Universal Mapper (`mapper.py`)

Transforms raw rows into strict **UniversalEvent** objects using fuzzy column matching.

| Semantic Field | Matched Keywords |
|----------------|------------------|
| `timestamp_col` | date, time, created, bill_date, invoice_date, trans_date, created_at |
| `amount_col` | amount, total, price, net, gross, revenue, sales, payment |
| `entity_col` | item, product, description, customer, vendor, name, sku |
| `reference_col` | id, order_id, invoice_no, bill_no, txn_id, receipt_no |

**Currency Handling:** Automatically strips `₹`, `$`, `€`, `£`, `Rs`, `INR`, commas, spaces.

**Example:** "Bill Dt" → `timestamp_col`, "Net Amt" → `amount_col`, "Rs 1,500.50" → `1500.5`

---

## 🏰 Phase 8 - Fortress Upgrade

**Mission:** Make ingestion faster, stricter, and resilient to missing master data.

### 1. The Bouncer (Schema Validation)
- Validates file schema before processing.
- Rejects junk/unknown files **early** (HTTP 400) if critical columns are missing.
- Uses filename + column hints for strict validation.

### 2. The Sherlock (Strict Classification)
- Classifies files as **STREAM** (Sales) or **STATE** (Menu).
- Weighted scoring: filename hints + column signals.
- Falls back to column-based classification when filename is weak.

### 3. Turbo Engine (Async Batch Classification)
- For large batches, processes events asynchronously in chunks of 50.
- Prevents timeouts on heavy uploads.

### 4. Ghost Logic (Resilient Item Handling)
- **STREAM:** Auto-creates provisional menu items for unknown sales entities.
- **STATE:** Upserts items and converts provisional items to official.
- Local registry file: `data/registry/<tenant>_category_registry.jsonl`.

---

## 🚀 Usage

### Endpoint
```
POST /api/v1/ingest/file
```

### Headers
| Header | Required | Description |
|--------|----------|-------------|
| `X-Tenant-ID` | ✅ Yes | Tenant identifier for multi-tenant isolation |
| `Content-Type` | Auto | `multipart/form-data` (handled by FastAPI) |

### Request Body
- `file`: The Excel or CSV file (form-data)

### Example (cURL)
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/file" \
  -H "X-Tenant-ID: cafe-mellow" \
  -F "file=@/path/to/sales_report.xlsx"
```

### Example (Python)
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/ingest/file",
    headers={"X-Tenant-ID": "cafe-mellow"},
    files={"file": open("sales_report.xlsx", "rb")}
)
print(response.json())
```

### Success Response (200 OK)
```json
{
  "status": "received",
  "filename": "sales_report.xlsx",
  "rows": 150,
  "columns": ["date", "amount", "description", "category"],
  "sample_data": [
    {"date": "2024-01-15", "amount": 1500.50, "description": "Sale Item A", "category": "Food"}
  ],
  "message": "Parsed 150 rows, mapped 148 to Universal Events",
  "header_row_detected": 0,
  "detection_method": "golden_path",
  "mapped_events": 148,
  "failed_events": 2,
  "column_mapping": {
    "timestamp_col": "date",
    "amount_col": "amount",
    "entity_col": "description",
    "reference_col": null
  },
  "sample_event": {
    "event_id": "abc123...",
    "tenant_id": "cafe-mellow",
    "timestamp": "2024-01-15T00:00:00",
    "amount": 1500.5,
    "entity_name": "Sale Item A",
    "category": "UNCATEGORIZED",
    "rich_data": "{...}"
  }
}
```

### Detection Methods
| Method | Description |
|--------|-------------|
| `golden_path` | Header found at Row 0 or 1 instantly |
| `deep_scan` | Header found after scanning (Row 2+) |
| `deep_scan_ambiguous` | Multiple candidates detected |
| `ai_judge` | AI resolved ambiguous case |

### Error Responses
| Status | Reason |
|--------|--------|
| 400 | Unsupported file format |
| 400 | Empty file |
| 400 | Rejected by Bouncer (unknown/junk schema) |
| 422 | Missing `X-Tenant-ID` header |
| 500 | Parse error (malformed file) |

---

## 🛡️ Safety Features

### 1. File Type Detection
- Extension-based detection (case-insensitive)
- Rejects dangerous file types immediately

### 2. Safe JSON Conversion
- All DataFrame data converted to `dict` via `.to_dict(orient='records')`
- NaN/NaT values replaced with empty strings
- DateTime columns converted to ISO strings

### 3. Column Sanitization
- Column names lowercased
- Spaces replaced with underscores
- Hyphens replaced with underscores
- Example: `"Order Date"` → `"order_date"`

### 4. Multi-Tenant Isolation
- Every request requires `X-Tenant-ID` header
- Tenant ID logged with every ingestion event
- Downstream processing respects tenant boundaries

---

## 🧪 Testing

### Run Verification Tests
```bash
python -X utf8 tests/verify_ingest_endpoint.py
```

### Test Results (Jan 30, 2026)
```
✅ PASS CSV Upload
✅ PASS Excel Upload
✅ PASS Bad File Type (400 rejection)
✅ PASS Missing Header (422 rejection)
✅ PASS Health Check

Total: 5/5 tests passed
```

---

## 🧠 The Self-Learning Loop

The Universal Adapter doesn't just process data—it **learns from mistakes**.

### How It Works

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────────────┐
│   Ingest    │ --> │  AI Classify │ --> │ Confidence     │ --> │  Main Ledger    │
│  (Upload)   │     │  (Gemini)    │     │    Check       │     │  (BigQuery)     │
└─────────────┘     └──────────────┘     └────────┬───────┘     └─────────────────┘
                                                  │
                                         ≥85% ───┘
                                         <85% ───┐
                                                  │
                                         ┌────────▼───────┐     ┌─────────────────┐
                                         │   Quarantine   │ --> │  Human Review   │
                                         │    Queue       │     │   (Approve)     │
                                         └────────────────┘     └────────┬────────┘
                                                                         │
                                                                         ▼
                                                                ┌─────────────────┐
                                                                │  Brain Learns   │
                                                                │ (Cache Updated) │
                                                                └─────────────────┘
```

### The Flow

1. **Ingest**: User uploads Excel/CSV file via `/api/v1/ingest/file`
2. **AI Classify**: `SemanticBrain` uses Gemini AI to categorize each row (SALES, INVENTORY, OVERHEAD, etc.)
3. **Confidence Check**: Traffic Cop routes events based on confidence score
   - **≥85% Confidence** → Main Ledger (`universal_ledger` table)
   - **<85% Confidence** → Quarantine Queue (for human review)
4. **Human Review**: User reviews quarantined items via `/api/v1/quarantine/list`
5. **Approve/Reject**: User resolves via `/api/v1/quarantine/resolve`
   - **APPROVE**: Event moves to Main Ledger + Brain learns the pattern
   - **REJECT**: Event is discarded
6. **Brain Learns**: Next time Brain sees similar item, it classifies correctly with 100% confidence

### Why This Matters

- **First time seeing "Kryptonite"**: AI confused → Quarantined (60% confidence)
- **Human approves as "EQUIPMENT"**: Brain caches the pattern
- **Second time seeing "Kryptonite"**: Brain knows → Main Ledger (100% confidence)

The system gets **smarter with every correction**.

---

## 🌐 API Endpoints

### Ingestion

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/ingest/file` | POST | Upload & process Excel/CSV file |
| `/api/v1/ingest/health` | GET | Health check for ingestion service |

### Quarantine (Human Review)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/quarantine/list` | GET | View quarantined items (requires `X-Tenant-ID`) |
| `/api/v1/quarantine/resolve` | POST | Approve or reject an item (teaches Brain) |
| `/api/v1/quarantine/stats` | GET | Get quarantine statistics |

### Example: Approve a Quarantined Item

```bash
curl -X POST "http://localhost:8000/api/v1/quarantine/resolve" \
  -H "X-Tenant-ID: cafe-mellow" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_abc123",
    "decision": "APPROVE",
    "correction": {"category": "EQUIPMENT", "sub_category": "special_items"},
    "reviewed_by": "admin"
  }'
```

**Response:**
```json
{
  "ok": true,
  "message": "Event approved, moved to ledger, brain updated",
  "event_id": "evt_abc123",
  "decision": "APPROVE",
  "learned": true
}
```

---

## 🔮 Roadmap

### ✅ Completed
- **Phase 2B:** Raw Ingestion Foundation (Excel/CSV parsing)
- **Phase 2C:** Structure Detective (Header Hunter)
- **Phase 2D:** AI Safety Net (Gemini Judge for ambiguity)
- **Phase 2E:** Universal Mapper (Fuzzy column matching)
- **Phase 3A:** Ledger Writer (Dual-mode BigQuery + Local)
- **Phase 3B:** Semantic Brain (AI Classification with cache)
- **Phase 3C:** Quarantine Queue (Traffic Cop routing)
- **Phase 3D:** Review API (Human feedback loop)

### 🔜 Next: Phase 4 - Universal Query Engine
- **Natural Language Queries:** "What were my sales yesterday?" → SQL → Answer
- **Smart Aggregations:** Auto-detect time ranges, groupings
- **Cross-Entity Analysis:** Join sales, inventory, expenses

### Future
- PDF table extraction (tabula-py)
- Image OCR for receipts (Google Vision API)
- Real-time streaming ingestion (webhooks)

---

## 📚 Related Modules

- **`backend/universal_adapter/structure_detective.py`** - Header row detection
- **`backend/universal_adapter/mapper.py`** - Fuzzy column mapping
- **`backend/universal_adapter/polymorphic_ledger.py`** - Universal event storage
- **`backend/universal_adapter/semantic_brain.py`** - AI classification
- **`backend/core/titan_v3/unified_engine.py`** - AI Judge (Gemini)
- **`pillars/config_vault.py`** - Centralized configuration

---

**Built with 🔥 by the TITAN Evolution Engine**
