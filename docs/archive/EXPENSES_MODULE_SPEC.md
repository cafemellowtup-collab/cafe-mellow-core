# Expenses Module — TITAN Spec

## 1. Data Model (expenses_master)

| Column         | Type   | Source / Logic |
|----------------|--------|----------------|
| expense_date   | DATE   | Date column from Excel |
| category       | STRING | Raw Reason/Category/Expense Head (unchanged) |
| ledger_name    | STRING | From " - " split: part before " - " (e.g. "Solar Maintenance") |
| main_category  | STRING | From " - " split: part after " - ", or "Uncategorized" |
| item_name      | STRING | Explanation/Description/Item Name |
| amount         | FLOAT  | Amount / Amount (₹) |
| payment_mode   | STRING | Paid From / Payment Mode |
| staff_name     | STRING | Created By / Employee / Staff / Entered By; "Unknown" if empty |
| remarks        | STRING | Remarks / Note |
| expense_id     | STRING | MD5 fingerprint for dedup |

**Dynamic Ledger Parsing:** Any value like `"Solar Maintenance - Repairs"` in Reason/Category is split into `ledger_name = "Solar Maintenance"` and `main_category = "Repairs"` automatically. New ledgers require no code change.

---

## 2. Expense Investigator (pre-query)

- **Trigger keywords:** electricity, electric, rent, salary, salaries, spend, spending, ledger, p&l, profit, loss, expense, expenses, house keeping, housekeeping.
- **Query:** `SELECT item_name, amount, expense_date, COALESCE(ledger_name, category) AS ledger_name, main_category FROM expenses_master WHERE (…keyword match on item_name, category, ledger_name, main_category…) [AND exclude_ledgers] [AND expense_date = yesterday if "yesterday"] ORDER BY expense_date DESC LIMIT 10`.
- **Exclude ledgers:** From `parse_excluded_ledgers(prompt)` — e.g. "ignore Rent, Electricity" → exclude those from WHERE. Applied to pre-query, trend, and narrative.

---

## 3. Trend Analysis (Expense Analysis Engine) — 3 Months

- **Inputs:** `exclude_ledgers` (optional), `ledger_focus` (optional). **Fetches last 3 months.**
- **Outputs:**
  - By ledger: This Month, Last Month, **2 Months Ago** spend; % Change; % of Revenue (This / Last); **Flag** (e.g. `CRITICAL ANOMALY`).
  - Totals: total_curr, total_last, total_m2; revenue_curr, revenue_last, revenue_m2; revenue_pct_change; curr_ratio, last_ratio.
- **Correlation / CRITICAL ANOMALY:** If Revenue is down ≥10% and a ledger (e.g. Electricity) is up ≥10% (vs last month), that row is flagged `CRITICAL ANOMALY` in the Markdown table.
- **Presentation:** Clean Markdown table. If user excluded ledgers, a note is included and ratios are recomputed excluding them.

---

## 4. Employee & Paid From (Who & How)

- **Query:** `GROUP BY staff_name, payment_mode` for last 7 days; `SUM(amount)`, `% of total`.
- **Example line:** "Employee 'Arun' has handled 70% of Cash expenses this week. Total: ₹X."
- **Table:** | Employee | Paid From | Amount (₹) | % of Total |

---

## 5. Response Format (Enforced)

1. **Tables** — Raw Facts (from pre-query), Trend (by ledger + totals + revenue ratios), Who & How (if available). Markdown only; no replacement by paragraphs.
2. **Trend Analysis** — Short narrative: This vs Last month, Expense/Revenue ratio, and, if applicable, exclusion note.
3. **Market Context** — Tiruppur/weather (e.g. high electricity ↔ 35–40°C and AC usage).

---

## 6. Exclude / Ignore Ledgers

- **User examples:** "Ignore Rent and Electricity and calculate P&L", "Exclude repairs for this month’s comparison."
- **Behavior:** `parse_excluded_ledgers(prompt)` extracts names; they are applied in:
  - Expense Investigator pre-query (WHERE exclusions),
  - Trend analysis (same),
  - AI instructions: "the data above already excludes them; mention that and give recalculated totals."

---

## 7. Evolution Lab (Suggested Pillars)

- When the AI infers that a **dedicated tracking pillar** would help (e.g. "Analyze the pattern of House Keeping salaries" → recurring salary/advance logic), it appends:  
  `SUGGESTED_PILLAR: Automated Salary & Advance Reconciliation Pillar`
- The app parses this, calls `log_evolution_pillar_suggestion(…)`, and removes the line from the displayed reply.

## 7b. IOT / Ledger Normalization (Self-Correction)

- If a ledger name looks like a **misspelling** of a canonical name (e.g. "Electrisity" vs "Electricity"), the engine’s `detect_ledger_misspellings` (difflib, cutoff=0.8) flags it.
- The app then logs an Evolution suggestion: **"Implement a Ledger Normalization Pillar to fix naming inconsistencies"** with details (e.g. `Detected: Electrisity → Electricity`).

---

## 8. Export

- **Download Markdown** — Full tables block (raw + trend + who/how).
- **Download CSV** — Raw expense rows, or trend by_ledger, or employee/payment rows, whichever is available.

---

## 9. Never Crash

- All BigQuery, regex, and AI calls are in try/except.
- Missing columns (e.g. `ledger_name` before first sync) fall back to `category`-only queries.
- On failure, return empty tables and a short error line; do not break the chat.

---

## 10. Integration (Future)

- Same pattern (pre-query, trend, exclude, who/how, Evolution, export) will extend to Sales, P&L, Purchases, Wastage.
- NL→SQL will expand to multi-table, multi-module queries.

---

*TITAN Expenses Module · Cafe Mellow · Tiruppur, Tamil Nadu*
