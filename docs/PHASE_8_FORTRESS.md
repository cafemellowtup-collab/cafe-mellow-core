# 🏰 Phase 8 - Fortress Upgrade (Data Ingestion)

**Status:** In Progress (Implementation Active)

## Overview
Phase 8 hardens ingestion with strict schema validation, deterministic classification, faster batch processing, and resilient handling of missing menu items.

## Goals
- **Accuracy:** Strict STREAM (Sales) vs STATE (Menu) classification
- **Safety:** Reject junk/unknown files before processing
- **Speed:** Async batch classification for large uploads
- **Resilience:** Auto-create provisional items when sales reference unknown menu data

---

## Core Components

### 1) The Bouncer (Schema Validation)
**Location:** `backend/universal_adapter/semantic_brain.py` + `api/routers/ingest.py`
- Validates critical columns **before** processing.
- Rejects junk/unknown files (HTTP 400) when schema is missing requirements.
- Uses filename + column hints (strict rules, no AI hallucination).

**Critical Columns**
- **STREAM (Sales):** date-like + amount-like
- **STATE (Menu):** item-like + price-like

**Behavior**
- If missing critical columns → **Reject**.
- If ambiguous → Sherlock classification used, then column-based fallback.

### 2) The Sherlock (Strict Classification)
**Location:** `backend/universal_adapter/semantic_brain.py`
- Determines `STREAM` vs `STATE` using weighted filename + column hints.
- Confidence is capped and transparent.
- If filename is weak, fallback to column-based signals (still strict).

### 3) Turbo Engine (Async Batch Classification)
**Location:** `backend/universal_adapter/semantic_brain.py` + `api/routers/ingest.py`
- Async batch classification in chunks of **50**.
- Prevents timeouts for large uploads.

### 4) Ghost Logic (Resilient Items)
**Location:** `backend/universal_adapter/ledger_writer.py`
- **STREAM:** Auto-create provisional menu items for unknown `entity_name`.
- **STATE:** Upsert items and convert provisional → official.
- Local registry: `data/registry/<tenant>_category_registry.jsonl`.

---

## Ingestion Flow (Phase 8)
```
Upload → Bouncer (Schema Validate) → Mapper → Sherlock → Turbo Classify → Ledger
                                            └─ Ghost Logic (STREAM/STATE)
```

---

## Expected Behaviors

### ✅ Sales.csv (new items)
- Classified as `STREAM`
- Provisional items created for unknown menu entities
- Events persisted to ledger

### ❌ Random.csv / Junk file
- Rejected by Bouncer with HTTP 400
- No background processing queued

### ✅ Menu.csv (STATE)
- Classified as `STATE`
- Provisional items converted to official

---

## Key Files Updated
- `backend/universal_adapter/semantic_brain.py`
- `backend/universal_adapter/ledger_writer.py`
- `api/routers/ingest.py`
- `backend/universal_adapter/README.md`

---

## Testing Checklist
1. Upload **Sales.csv** with new items → provisional items created.
2. Upload **Random.csv** → HTTP 400 rejection.
3. Upload **Sales.csv** again → duplicates skipped by existing ledger logic.
4. Upload **Menu.csv** → provisional items marked official.

---

## Notes
- This phase prioritizes **deterministic validation** over AI guesses.
- If filename hints are weak, classification relies on column signals.
