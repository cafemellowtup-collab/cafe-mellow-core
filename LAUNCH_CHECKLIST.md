# Launch Checklist (Cafe_AI)

Use this before you share a build/demo or deploy.

## 1) Start the dev stack
- Run `scripts/start_dev.ps1`
- Confirm you have:
  - Web: http://localhost:3000
  - API: http://127.0.0.1:8000

## 2) Confirm API health
Open:
- http://127.0.0.1:8000/health

You should see:
- `ok: true`
- `bq_connected: true`
- correct `project_id` and `dataset_id`

## 3) Quick Operations checks (2 minutes)
Open:
- http://localhost:3000/operations

### Expenses tab
- Pick a date range that definitely has data
- Click Apply/Refresh
- Confirm:
  - Total amount is shown
  - Row count is shown
  - Table shows rows
- Change 1 filter (example: Ledger) and re-apply
- Click Export CSV and confirm a file downloads

### Sales tab
- Click Refresh
- Confirm:
  - Revenue by order type has rows
  - Revenue by delivery partner has rows
  - Top items has rows
- Click Export CSV and confirm a file downloads

## 4) If something looks wrong
- First open these URLs in the browser (they must return JSON, not an error):
  - http://127.0.0.1:8000/ops/expenses?start=2025-12-01&end=2026-01-23&limit=5
  - http://127.0.0.1:8000/ops/sales/channels?start=2025-12-01&end=2026-01-23
  - http://127.0.0.1:8000/ops/sales/top-items?start=2025-12-01&end=2026-01-23&limit=10

If any URL shows an error, copy-paste the exact error text.
