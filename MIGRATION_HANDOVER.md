# MIGRATION_HANDOVER.md

## Core Features (Implemented & Wired)

### Backend (FastAPI)
- Universal ingestion pipeline (upload → raw logs → processing → ledger/quarantine).
- AI chat endpoints (streaming + non-streaming) tied to BigQuery query engine.
- Ops brief generation + AI task queue generation.
- Self-healing Phoenix Protocols + stats endpoint.
- BigQuery cost guardrails and system logs (system_error_log, system_sync_log).
- Auth endpoints (signup/login/verify/logout) with JWT token support.

### Frontend (Next.js App Router)
- Dashboard landing with multi-file upload and status feedback.
- Data page for file ingestion status and processing metrics.
- Chat UI with streaming UX and suggested prompts.
- Settings page with system status + factory reset trigger.
- Shared AppLayout with sidebar navigation and header.

### Admin / Ops
- Streamlit command center (titan_app.py) for ops monitoring and configuration.
- Scheduler + cron endpoints (Cloud Scheduler compatible).

---

## Known Bugs / Critical Risks (Build & Runtime)

1. **Frontend API client may be missing in IDX builds**
   - Root `.gitignore` previously ignored `frontend/lib/` (now overridden).
   - `frontend/app/*` imports `@/lib/api`, so ensure `frontend/lib/api.ts` is tracked after `git add`.

2. **Potential runtime error with next-themes**
   - `components/ui/sonner.tsx` uses `useTheme` but no ThemeProvider is present in `frontend/app/layout.tsx`.
   - **Fix:** wrap root layout with `ThemeProvider` from `next-themes`.

3. **Documentation paths mismatch**
   - README references `/web` directory; actual Next.js app is under `/frontend`.
   - Not build-blocking, but confusing during migration.

---

## Environment Variables (.env)

> **List of required/optional variable names (no values):**

### Core / AI
- GEMINI_API_KEY
- GEMINI_URL

### BigQuery / GCP
- PROJECT_ID
- DATASET_ID
- BQ_DATASET
- GOOGLE_CLOUD_PROJECT
- GOOGLE_APPLICATION_CREDENTIALS

### Petpooja
- PP_APP_KEY
- PP_APP_SECRET
- PP_ACCESS_TOKEN
- PP_MAPPING_CODE

### Drive Folders
- FOLDER_ID_EXPENSES
- FOLDER_ID_CASH_OPS
- FOLDER_ID_PURCHASES
- FOLDER_ID_INVENTORY
- FOLDER_ID_RECIPES
- FOLDER_ID_WASTAGE

### Folder Watcher (Archive/Failed)
- TITAN_ARCHIVED_EXPENSES
- TITAN_FAILED_EXPENSES
- TITAN_ARCHIVED_PURCHASES
- TITAN_FAILED_PURCHASES
- TITAN_ARCHIVED_INVENTORY
- TITAN_FAILED_INVENTORY
- TITAN_ARCHIVED_RECIPES
- TITAN_FAILED_RECIPES
- TITAN_ARCHIVED_WASTAGE
- TITAN_FAILED_WASTAGE

### Budget / Cost Guardrails
- BUDGET_MONTHLY_INR
- MAX_QUERY_COST_INR
- DISABLE_BUDGET_BREAKER
- BIGQUERY_USD_PER_TB
- USD_TO_INR

### Security / Auth / Automation
- CRON_SECRET
- JWT_SECRET
- SYNC_TRIGGERED_BY

### Optional Storage (R2)
- R2_ACCOUNT_ID
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET_NAME
