# TITAN Vision

## Purpose

TITAN is the Self-Developing, Petpooja-Rivaling Intelligence ERP for Cafe Mellow and similar F&B operations. The vision is to combine **real-time data (Google Drive → BigQuery)**, **natural-language understanding**, and **automated analytics** so that owners and managers get **exact, table-first answers** instead of generic paragraphs.

## Principles

1. **Table-first, then analysis, then context** — Every expense, P&L, or comparison answer leads with raw-fact tables, then trend analysis, then Tiruppur/market context.
2. **Dynamic structure** — Ledgers and categories adapt from the " - " convention (e.g. "Solar Maintenance - Repairs") without code changes.
3. **Exclude and recalculate** — Users can say "ignore Rent and Electricity and calculate P&L"; the system excludes those ledgers and recomputes totals and ratios.
4. **Who & How** — Track who (Employee) spent and how (Paid From) for accountability and audits.
5. **Evolution memory** — When a query reveals the need for a dedicated pillar (e.g. Salary & Advance Reconciliation), it is logged in Evolution Lab for prioritization.
6. **Export and reuse** — Tables and charts are downloadable (Markdown, CSV) for reports and further analysis.
7. **Never crash** — All BigQuery, parsing, and AI flows are wrapped in safe fallbacks so the app stays up.

## Scope (phased)

- **Phase 1 (current): Expenses** — Ledger parsing, trend analysis, exclude ledgers, employee/payment breakdown, Evolution suggestions, export.
- **Phase 2:** Sales, P&L, inventory, wastage, purchases.
- **Phase 3:** Full NL→SQL across all modules; charts and dashboards as exportable artifacts.

---

*TITAN Command Center · Cafe Mellow · Tiruppur, Tamil Nadu*
