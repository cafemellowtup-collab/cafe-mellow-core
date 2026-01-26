# TITAN Mission

## Mission

To give Cafe Mellow (and similar F&B businesses) **forensic-grade expense and business intelligence** through:

1. **Deep Context Injection** — Before the AI answers, run pre-queries (Expense Investigator, Trend, Employee/Paid From) and inject real BigQuery rows and tables into the prompt so answers use **exact figures**, not estimates.
2. **Natural English → SQL → Perfect Output** — The system interprets normal questions (including "ignore X and calculate P&L"), infers filters and groupings, runs safe SQL, and returns tables plus narrative. This is implemented first for **expenses** and will extend to other modules.
3. **Structured, Exportable Answers** — Every response is: **Tables (raw + trend + who/how)** → **Trend Analysis** → **Market Context (Tiruppur/weather)**. Tables and charts are downloadable (Markdown, CSV).
4. **Self-Improvement** — When the AI identifies a need for a dedicated tracking pillar, it logs to Evolution Lab (e.g. "Suggested: Automated Salary & Advance Reconciliation Pillar") so the product can evolve.

## Success Criteria

- "How much was electricity yesterday?" → exact ₹ from `expenses_master`.
- "Ignore Rent and Electricity and calculate P&L" → recalculated totals and ratios excluding those ledgers.
- "Analyze the pattern of House Keeping salaries" → table, trend, and optional Evolution suggestion for a Salary/Advance pillar.
- "Who handled Cash expenses this week?" → Employee × Paid From table with % of total.
- All of the above: tables first, then analysis, then Tiruppur context; no crashes; exportable.

---

*TITAN Command Center · Cafe Mellow · Tiruppur, Tamil Nadu*
