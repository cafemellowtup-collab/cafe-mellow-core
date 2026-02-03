# FUTURE_ROADMAP.md

## Credit-Burner Analysis (IDX Migration Ready)

### Snapshot (Current Architecture)
- Frontend: Next.js 16 App Router (frontend/)
- Backend: FastAPI (api/) + Streamlit admin (titan_app.py)
- Data: BigQuery (config via pillars/config_vault.py)
- AI: Gemini (google.genai)
- Self-Healing: Phoenix Protocols (backend/core/titan_v3/phoenix_protocols.py)
- Deployment: Vercel (frontend), Cloud Run/VM (backend)

---

## 1) Refactoring Plan (Spaghetti Hotspots)

### Priority 1: Break the Monoliths
1. api/main.py (1500+ lines)
   - Problem: startup, scheduler, routing, and logic mixed in one file.
   - Refactor: extract app factory, background scheduler, router registry, and settings into separate modules.
   - Result: faster cold starts, clearer boundaries, easier testing.

2. backend/universal_adapter/semantic_brain.py (1300+ lines)
   - Problem: classifier, prompt logic, caching, and schema logic in one file.
   - Refactor: split into services: classifier.py, schema_generator.py, prompt_templates.py, cache.py.

3. backend/universal_adapter/refinery.py + processor.py + guard.py
   - Problem: duplicated BigQuery client init + mixed IO/transform logic.
   - Refactor: move all BigQuery initialization into utils/bq_client.py and use a shared data-access layer.

### Priority 2: Isolate Cross-Cutting Concerns
4. titan_app.py (Streamlit admin, ~700 lines)
   - Problem: UI and service logic are tightly coupled.
   - Refactor: extract service layer into pillars/ or backend/services/; keep Streamlit as a thin UI.

5. backend/core/titan_v3/phoenix_protocols.py
   - Problem: self-healing logic, persistence, and patch execution in one class.
   - Refactor: split into HealingStateMachine, PatchExecutor, PatchRegistry, HealingLogRepository.

6. settings.py + config_vault.py
   - Problem: hardcoded IDs in settings.py plus mixed override logic.
   - Refactor: move all IDs to env/config_vault; add typed schema validation and env loading.

### Priority 3: Frontend Structure
7. frontend/app
   - Problem: page-level logic uses direct API calls with no central error boundary.
   - Refactor: introduce a client SDK layer + centralized error boundary + typed API client.

---

## 2) Robustness Strategy for Self-Healing (3 Specific Moves)

1. Finite State Machine + Idempotent Transitions
   - Implement a strict state machine (DETECTED -> ANALYZING -> PATCHING -> TESTING -> HEALED/FAILED).
   - Persist every transition with idempotency keys in BigQuery (titan_healing_log).
   - Prevent double-patching and ensure retries are safe.

2. Sandbox Patch Validation Pipeline
   - Execute generated patches in a sandbox process with timeouts.
   - Run contract tests (golden inputs) and static checks (ast + lint) before hot-patch.
   - Block patches that touch unsafe imports or filesystem/network beyond scope.

3. Patch Registry + Rollback + Human-in-the-Loop
   - Store every patch version in GCS with hash + metadata (confidence, tests passed).
   - Add a circuit breaker: auto-disable healing if failure rate crosses threshold.
   - Require manual approval for low-confidence patches or production rollouts.

---

## 3) BigQuery Scalability Plan (10,000 Users)

1. Table Design
   - Use a single canonical ledger table partitioned by ingestion_date and clustered by tenant_id, location_id, category.
   - Keep raw_ingest and canonical datasets separate.
   - Use row-level security policies on tenant_id.

2. Tenant & Billing Tables
   - Add tenants, users, org_locations, billing_plans, api_keys.
   - Use authorized views for per-tenant data access.

3. Performance + Cost Controls
   - Materialized views for daily rollups.
   - TTL policies on raw logs.
   - BigQuery reservations for predictable costs.

4. Ingestion Reliability
   - Deduplicate by event_id + schema_fingerprint.
   - Store ingestion checkpoints to support replay and reprocessing.

---

## 4) Gap Analysis (What’s Missing for “Product”)

1. Reliability & Operations
   - Message queue for ingestion (Cloud Tasks / PubSub)
   - Dead-letter queue for failed transformations
   - Idempotency keys on all write endpoints

2. Security
   - Rate limiting for APIs
   - Auth enforcement on all routers
   - Secret Manager integration for keys

3. Observability
   - Structured logging + OpenTelemetry tracing
   - Error tracking (Sentry/GCP Error Reporting)
   - Health checks per subsystem

4. Frontend Hardening
   - Global error boundary
   - Loading/skeleton states and retry UI
   - 404/500 pages and offline handling

5. CI/CD & Testing
   - Unit tests for AI transforms and schema validation
   - Integration tests for ingest, chat, and analytics endpoints
   - CI pipeline with lint + typecheck

---

## 5) Ultra-Modernization Track (IDX-First)

1. Architecture
   - Monorepo via Turborepo or pnpm workspaces
   - Typed API contracts (OpenAPI or tRPC)

2. AI Stack
   - Gemini 2.5 Pro + tool calling for deterministic actions
   - Use BigQuery vector search for embeddings + RAG

3. Serverless Scale
   - Cloud Run Jobs for scheduled ingestion
   - Pub/Sub for event-driven orchestration

4. Frontend
   - Next.js server actions for data access
   - Streaming UI for chat + analytics
   - Progressive rendering and skeletons
