"""
Enhanced Chat: Gemini/ChatGPT-style UI, History Panel (max 30), Auto-naming,
350-turn limit, Export/Copy on tables, Anomaly banner.
"""
import streamlit as st
import re
import io
import csv
import pandas as pd
from utils.gemini_chat import chat_with_gemini, get_bigquery_context
from utils.advanced_query_engine import AdvancedQueryEngine
from utils.ai_agent import TitanAIAgent
from pillars.chat_intel import expense_investigator_prequery, heuristic_filter_expenses, get_categorized_table, parse_time_window
from pillars.expense_analysis_engine import (
    parse_excluded_ledgers,
    run_expense_trend_analysis,
    run_employee_payment_analysis,
    format_trend_markdown,
    format_employee_payment_markdown,
    detect_ledger_misspellings,
    calculate_discretionary_spend,
    get_power_contingency_vs_eb,
)
from pillars.evolution import log_evolution_pillar_suggestion

MAX_CHATS = 30
MAX_TURNS = 350


def _ensure_chat_limit(sessions, order):
    """Keep at most MAX_CHATS; drop oldest by order."""
    while len(order) > MAX_CHATS and order:
        oldest = order.pop()
        sessions.pop(oldest, None)


def _table_export_copy(md, raw, trend, emp, key_suffix="0"):
    """Render [Copy Markdown] and [Download CSV] immediately; then st.code for markdown."""
    if not (md or raw or (trend and trend.get("by_ledger")) or emp):
        return
    c1, c2 = st.columns(2)
    with c1:
        if md:
            st.download_button("[Copy Markdown]", md, file_name="titan_tables.md", mime="text/markdown", use_container_width=True, key=f"dl_md_{key_suffix}")
    with c2:
        try:
            buf = io.StringIO()
            w = csv.writer(buf)
            if raw and len(raw) > 0:
                keys = list(raw[0].keys())
                w.writerow(keys)
                for r in raw:
                    w.writerow([r.get(k, "") for k in keys])
            elif trend and trend.get("by_ledger"):
                w.writerow(["ledger_name", "curr_spend", "last_spend", "m2_spend", "pct_change", "curr_pct_rev", "last_pct_rev", "anomaly"])
                for r in trend["by_ledger"]:
                    w.writerow([r.get("ledger_name",""), r.get("curr_spend",0), r.get("last_spend",0), r.get("m2_spend",0), r.get("pct_change",0), r.get("curr_pct_rev",0), r.get("last_pct_rev",0), r.get("anomaly","")])
            elif emp:
                w.writerow(["staff_name", "payment_mode", "amount", "pct_of_total"])
                for r in emp:
                    w.writerow([r.get("staff_name",""), r.get("payment_mode",""), r.get("amount",0), r.get("pct_of_total",0)])
            csv_str = buf.getvalue()
            if csv_str:
                st.download_button("[Download CSV]", csv_str, file_name="titan_tables.csv", mime="text/csv", use_container_width=True, key=f"dl_csv_{key_suffix}")
        except Exception:
            pass
    if md:
        st.caption("Markdown (select and Ctrl+C to copy):")
        st.code(md, language="markdown")


def render_enhanced_chat_interface(client, settings, on_assistant_response=None):
    # --- Session state ---
    if "chat_sessions" not in st.session_state:
        st.session_state.chat_sessions = {}
        st.session_state.current_chat_id = "default"
        st.session_state.chat_order = []
    if "chat_order" not in st.session_state:
        st.session_state.chat_order = list(st.session_state.chat_sessions.keys())
    if "chat_data_sources" not in st.session_state:
        st.session_state.chat_data_sources = {}
    if "last_tables_md" not in st.session_state:
        st.session_state.last_tables_md = ""
    if "last_tables_raw" not in st.session_state:
        st.session_state.last_tables_raw = []
    if "last_tables_trend" not in st.session_state:
        st.session_state.last_tables_trend = {}
    if "last_tables_employee" not in st.session_state:
        st.session_state.last_tables_employee = []
    if "query_engine" not in st.session_state:
        st.session_state.query_engine = AdvancedQueryEngine(client, settings)
        st.session_state.ai_agent = TitanAIAgent(client, settings)
    if "default" not in st.session_state.chat_sessions:
        st.session_state.chat_sessions["default"] = {"name": "New Chat", "messages": []}
        st.session_state.chat_order = ["default"] + [k for k in st.session_state.chat_order if k != "default"]

    current_chat = st.session_state.chat_sessions.get(st.session_state.current_chat_id, {"name": "New Chat", "messages": []})

    # --- Anomaly banner (FIRST; integrate from Dashboard) ---
    try:
        from pillars.dashboard import get_anomaly_status
        an = get_anomaly_status(client, settings, days=7)
        if an.get("detected"):
            st.error("ANOMALY: " + (an.get("msg") or "") + " Review revenue and cost controls.")
    except Exception:
        pass

    # --- Layout: main (left) + History (right) ---
    main_col, hist_col = st.columns([4, 1])
    with main_col:
        # Compact header
        st.markdown("""
        <div style="padding: 0.75rem 1rem; background: linear-gradient(90deg, #1a1f2e 0%, #252b3b 100%); border-radius: 12px; margin-bottom: 1rem; border: 1px solid rgba(255,255,255,0.06);">
        <span style="color: #e6edf3; font-weight: 600;">TITAN</span> <span style="color: #8b949e;">· Ask expenses, sales, P&L, staff</span>
        </div>
        """, unsafe_allow_html=True)

        # New / Clear
        r1, r2 = st.columns([1, 5])
        with r1:
            if st.button("+ New", key="btn_new_chat", use_container_width=True):
                new_id = f"chat_{len(st.session_state.chat_sessions)}_{id(object())}"
                st.session_state.chat_sessions[new_id] = {"name": "New Chat", "messages": []}
                st.session_state.chat_order = [new_id] + [k for k in st.session_state.chat_order if k != new_id]
                _ensure_chat_limit(st.session_state.chat_sessions, st.session_state.chat_order)
                st.session_state.current_chat_id = new_id
                st.rerun()
            if st.button("Clear", key="btn_clear_chat", use_container_width=True):
                st.session_state.chat_sessions[st.session_state.current_chat_id]["messages"] = []
                st.session_state.last_tables_md = ""
                st.session_state.last_tables_raw = []
                st.session_state.last_tables_trend = {}
                st.session_state.last_tables_employee = []
                st.rerun()

        # Data Sources expander with Export/Copy
        with st.expander("Data sources & Export", expanded=False):
            ds = st.session_state.get("chat_data_sources", {})
            exp_rows = ds.get("expense_rows") or []
            if exp_rows:
                st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
                _table_export_copy("", exp_rows, {}, [])
            md = st.session_state.get("last_tables_md", "")
            raw = st.session_state.get("last_tables_raw", [])
            trend = st.session_state.get("last_tables_trend", {})
            emp = st.session_state.get("last_tables_employee", [])
            if md or raw or (trend and trend.get("by_ledger")) or emp:
                if raw:
                    st.dataframe(pd.DataFrame(raw), use_container_width=True, hide_index=True)
                _table_export_copy(md, raw, trend, emp)

        # Messages (350-turn cap: only keep last MAX_TURNS*2 when appending is done below)
        for idx, msg in enumerate(current_chat.get("messages", [])):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("role") == "assistant" and (msg.get("tables_md") or msg.get("tables_raw")):
                    with st.expander("📊 Supporting data", expanded=False):
                        if msg.get("tables_md"):
                            st.markdown(msg["tables_md"])
                        _table_export_copy(msg.get("tables_md",""), msg.get("tables_raw",[]), msg.get("tables_trend",{}), msg.get("tables_employee",[]), f"m{st.session_state.current_chat_id}_{idx}")

        # Input
        if prompt := st.chat_input("Ask about your business..."):
            msgs = current_chat.get("messages", [])
            # Auto-naming: from first two messages after we have 2 (handled below when assistant is appended)
            msgs.append({"role": "user", "content": prompt})
            # 350-turn cap
            if len(msgs) > MAX_TURNS * 2:
                msgs = msgs[-(MAX_TURNS * 2):]
            current_chat["messages"] = msgs

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                st.caption("⏳ Thinking...")
                response = None
                excl = []
                try:
                    excl = parse_excluded_ledgers(prompt)
                except Exception:
                    pass
                pre_rows, pre_kw = [], []
                try:
                    pre_rows, pre_kw = expense_investigator_prequery(client, settings, prompt, exclude_ledgers=excl or None)
                    pre_rows = pre_rows or []
                except Exception:
                    pre_rows, pre_kw = [], []
                heuristic_rows, h_kw = [], []
                cat_md = ""
                if any(x in prompt.lower() for x in ["electricity", "electric", "eb", "power", "diesel", "generator", "category", "core", "contingency", "main utility"]):
                    try:
                        heuristic_rows, h_kw = heuristic_filter_expenses(client, settings, prompt, exclude_ledgers=excl or None)
                        if heuristic_rows:
                            cat_md = get_categorized_table(heuristic_rows)
                    except Exception:
                        pass
                discretionary_md = ""
                _amt_m = (
                    re.search(r'cover\s*(?:Rs?\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', prompt, re.I)
                    or re.search(r'set aside\s*(?:Rs?\.?|₹)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', prompt, re.I)
                    or re.search(r'(?:Rs?\.?|₹)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:for|to)\s*(?:a?\s*staff|pongal|celebration|cover|budget|trip)', prompt, re.I)
                    or re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:to cover|for (?:discretionary|trip|budget|sales push)|on (?:discretionary|trip|budget))', prompt, re.I)
                )
                _days_avail = None
                if "this weekend" in prompt.lower() or "weekend" in prompt.lower():
                    _days_avail = 2
                elif "per day" in prompt.lower():
                    _days_avail = 7
                if _amt_m and client and settings:
                    try:
                        _amt = float(_amt_m.group(1).replace(",", ""))
                        _d = calculate_discretionary_spend(client, settings, _amt, days_available=_days_avail)
                        if _d.get("sales_push") is not None:
                            discretionary_md = f"### Budget/Trip: Sales Push\nTo cover ₹{_amt:,.2f}: Sales Push = ₹{_d['sales_push']:,.2f} (7d margin {_d.get('profit_margin_pct')}%)."
                            if _d.get("sales_push_per_day") is not None and _days_avail:
                                discretionary_md += f" Over {_days_avail} days: **₹{_d['sales_push_per_day']:,.2f} extra per day**."
                        elif _d.get("error"):
                            discretionary_md = f"### Budget/Trip\n{_d['error']}"
                    except Exception:
                        pass
                st.session_state.chat_data_sources = {"expense_rows": pre_rows, "expense_keywords": pre_kw, "last_prompt": prompt}

                trend_data = {}
                emp_data = []
                trend_md = ""
                emp_md = ""
                if pre_kw:
                    try:
                        trend_data = run_expense_trend_analysis(client, settings, exclude_ledgers=excl or None)
                        trend_md = format_trend_markdown(trend_data)
                    except Exception:
                        pass
                    try:
                        emp_data = run_employee_payment_analysis(client, settings, days=7)
                        emp_md = format_employee_payment_markdown(emp_data, 7)
                    except Exception:
                        pass

                raw_facts_md = ""
                if pre_rows:
                    raw_facts_md = "### Raw Facts\n| Item | Amount | Date | Ledger |\n|------|--------|------|--------|\n"
                    for r in pre_rows:
                        raw_facts_md += f"| {(r.get('item_name') or '').replace('|','\\|')} | {r.get('amount',0):,.2f} | {r.get('expense_date','')} | {(r.get('ledger_name') or '').replace('|','\\|')} |\n"
                _parts = [p for p in [trend_md, raw_facts_md, cat_md, discretionary_md, emp_md] if p]
                tables_block = "\n\n".join(_parts).strip()
                factual_block = "FACTUAL DATA:\n" + tables_block if tables_block else ""

                parsed = st.session_state.query_engine.parse_query(prompt)
                if parsed:
                    try:
                        res = st.session_state.query_engine.execute_query(parsed)
                        if res:
                            response = res
                    except Exception:
                        pass

                if not response:
                    try:
                        context = get_bigquery_context(client, settings, limit=20)
                    except Exception:
                        context = ""
                    history = []
                    for m in msgs[-10:]:
                        if m["role"] == "user":
                            history.append({"user_message": m["content"], "ai_response": ""})
                        elif m["role"] == "assistant" and history:
                            history[-1]["ai_response"] = m["content"]
                    try:
                        from utils.market_intelligence import MarketIntelligence
                        mi = MarketIntelligence()
                        market_context = mi.get_market_context()
                        weather_insights = mi.get_weather_insights()
                    except Exception:
                        market_context = "Tiruppur, Tamil Nadu"
                        weather_insights = "Hot season 35–40°C; AC can raise electricity costs."
                    _messy = """
MESSY DATA: The Explanation (item_name) column has real-world typos (e.g. 'diesal','disal','EB man'). Treat: diesel/generator/motor variants = Group B (Power Contingency); EB/electric = Group A (Main Utility); service/tips = Group C (Maintenance). If you see a description that might match multiple ledgers (e.g. 'Ganga Payment' vs 'Ganga Chit'), ask: "I see '[X]'—is this the same as your '[Y]' ledger?"
"""
                    _style = """
HUMAN ANALYSIS STYLE — apply to ALL expense categories and every answer:
1) State the numbers clearly (totals, % of revenue, change vs last month).
2) Compare: to revenue, to prior period, and where the data allows, break down sub-parts (e.g. for power: contingency vs main EB; for other categories: core vs one-off if item names suggest it).
3) Caveats: when the ask does not match the data (e.g. "last 30 days" but no entries in that window), say so plainly and use the nearest available period or the most recent entries.
4) Bottom line: one clear takeaway or action (e.g. "Contingency is X% of your EB; consider reducing cuts" or "To cover ₹X you need ₹Y extra sales; that is ₹Z per day over N days").
Write like a sharp, friendly business advisor: direct, human, and practical. No robotic bullet lists only—weave the facts into a concise narrative. Do NOT reproduce the FACTUAL DATA tables or raw markdown in your reply; synthesize them into a human narrative. For "cover Rs X" / "set aside Rs X" / "how much to sell": use the Budget/Trip block; if the user asked "per day" or "this weekend", lead with the per-day number.
"""
                    enhanced_prompt = f"""You are TITAN, AI business assistant for Cafe Mellow, Tiruppur.
{_messy}
{_style}
Context: {context}
Market: {market_context}
Weather: {weather_insights}
{factual_block}

User: {prompt}

If revenue down ≥10% and a ledger up ≥10%, say "CRITICAL ANOMALY". Use only the factual data. End with SUGGESTED_PILLAR: <name> only if a new tracking pillar would help; else omit."""
                    try:
                        response = chat_with_gemini(client, settings, enhanced_prompt, history, use_enhanced_prompt=True, original_user_prompt=prompt)
                    except Exception as e:
                        response = f"Request failed: {e}"

                if response:
                    to_show = response
                    _raw = pre_rows if pre_rows else (heuristic_rows if cat_md else [])
                    m = re.search(r"SUGGESTED_PILLAR:\s*(.+?)(?:\n|$)", response, re.I)
                    if m and client and settings:
                        try:
                            log_evolution_pillar_suggestion(client, settings, prompt[:2000], m.group(1).strip(), "From query.")
                            to_show = re.sub(r"\n?SUGGESTED_PILLAR:\s*.+", "", response, flags=re.I).strip()
                        except Exception:
                            pass
                    try:
                        ledgers = [str(r.get("ledger_name") or "").strip() for r in (trend_data.get("by_ledger") or [])] + [str(r.get("ledger_name") or "").strip() for r in pre_rows]
                        ledgers = [x for x in ledgers if x]
                        miss = detect_ledger_misspellings(ledgers)
                        if miss and client and settings:
                            log_evolution_pillar_suggestion(client, settings, prompt[:1500], "Ledger Normalization Pillar", "; ".join(f"'{a}'→'{b}'" for a, b in miss[:5]))
                    except Exception:
                        pass
                    final_content = to_show
                    st.session_state.last_tables_md = tables_block
                    st.session_state.last_tables_raw = _raw
                    st.session_state.last_tables_trend = trend_data
                    st.session_state.last_tables_employee = emp_data
                    if callable(on_assistant_response):
                        try:
                            on_assistant_response(client, settings, prompt, final_content)
                        except Exception:
                            pass
                    st.markdown(final_content)
                    if tables_block:
                        with st.expander("📊 Supporting data", expanded=False):
                            st.markdown(tables_block)
                            _table_export_copy(tables_block, _raw, trend_data, emp_data, "curr0")
                    asst_msg = {"role": "assistant", "content": final_content}
                    if tables_block or _raw or (trend_data and trend_data.get("by_ledger")) or emp_data:
                        asst_msg["tables_md"] = tables_block
                        asst_msg["tables_raw"] = _raw
                        asst_msg["tables_trend"] = trend_data
                        asst_msg["tables_employee"] = emp_data
                    msgs = current_chat.get("messages", [])
                    msgs.append(asst_msg)
                    if len(msgs) > MAX_TURNS * 2:
                        msgs = msgs[-(MAX_TURNS * 2):]
                    current_chat["messages"] = msgs
                    # Auto-naming from first two messages
                    if current_chat.get("name") == "New Chat" and len(msgs) >= 2:
                        _a = (msgs[0].get("content") or "")[:25]
                        _b = (msgs[1].get("content") or "")[:20]
                        current_chat["name"] = (_a + " + " + _b).strip(" +") or "Chat"

            st.session_state.chat_sessions[st.session_state.current_chat_id] = current_chat
            st.rerun()

    # --- Right: History (max 30) ---
    with hist_col:
        st.markdown("**History**")
        order = st.session_state.get("chat_order", [])[:MAX_CHATS]
        for cid in order:
            data = st.session_state.chat_sessions.get(cid, {})
            name = (data.get("name") or "Chat")[:28] + ("…" if len((data.get("name") or "")) > 28 else "")
            is_cur = cid == st.session_state.current_chat_id
            lbl = ("▶ " if is_cur else "") + name
            if st.button(lbl, key=f"hist_{cid}", use_container_width=True):
                if cid != st.session_state.current_chat_id:
                    st.session_state.current_chat_id = cid
                    st.rerun()
        st.caption(f"Max {MAX_CHATS} chats")
