"""
TITAN Gemini Chat Integration with Advanced AI Memory and Learning
Enhanced with Phoenix Protocols and Evolution Core Integration
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from utils.bq_guardrails import query_to_df

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from backend.core.titan_v3.evolution_core import EvolutionCore
    from backend.core.titan_v3.phoenix_protocols import PhoenixProtocols
except ImportError:
    EvolutionCore = None
    PhoenixProtocols = None



def get_enhanced_bigquery_context(client, settings, user_message: str = "", limit: int = 10) -> Dict[str, Any]:
    """Enhanced BigQuery context with TITAN intelligence and learning integration"""
    context_data = {
        "sales_data": None,
        "financial_summary": None,
        "alerts": None,
        "learned_patterns": None,
        "ai_insights": []
    }
    
    # Initialize Evolution Core for learning integration
    evolution = None
    if EvolutionCore:
        try:
            evolution = EvolutionCore()
            if user_message:
                learned_context = evolution.build_learning_context(user_message)
                if learned_context:
                    context_data["learned_patterns"] = learned_context
        except Exception:
            pass
    
    try:
        # Enhanced sales data context
        try:
            q_sales = f"""
                SELECT 
                    bill_date, 
                    customer_name,
                    table_number,
                    order_type,
                    delivery_partner,
                    item_name, 
                    quantity, 
                    total_revenue,
                    payment_mode,
                    coupon_codes,
                    advance_order
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_enhanced`
                ORDER BY bill_date DESC
                LIMIT {limit}
            """
            
            sales_df, _ = query_to_df(client, settings, q_sales, purpose=f"chat.context.sales_enhanced_limit_{int(limit)}")
            if not sales_df.empty:
                context_data["sales_data"] = {
                    "type": "enhanced",
                    "records": len(sales_df),
                    "summary": sales_df[['bill_date', 'customer_name', 'order_type', 'item_name', 'total_revenue', 'payment_mode']].to_dict('records')[:5],
                    "formatted": sales_df[['bill_date', 'customer_name', 'order_type', 'item_name', 'total_revenue', 'payment_mode']].to_string(index=False)
                }

        except Exception:
            # Fallback to basic parsed table
            try:
                q_sales = f"""
                    SELECT bill_date, item_name, quantity, total_revenue 
                    FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed`
                    ORDER BY bill_date DESC
                    LIMIT {limit}
                """
                sales_df, _ = query_to_df(client, settings, q_sales, purpose=f"chat.context.sales_items_parsed_limit_{int(limit)}")
                if not sales_df.empty:
                    context_data["sales_data"] = {
                        "type": "basic",
                        "records": len(sales_df),
                        "formatted": sales_df.to_string(index=False)
                    }
            except Exception:
                pass

        # Get recent AI tasks and alerts with enhanced intelligence
        try:
            q_tasks = f"""
                SELECT task_type, item_involved, description, priority, status, created_at
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.ai_task_queue`
                WHERE status = 'Pending'
                ORDER BY 
                    CASE priority 
                        WHEN 'Critical' THEN 1
                        WHEN 'High' THEN 2  
                        WHEN 'Medium' THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT 5
            """
            tasks_df, _ = query_to_df(client, settings, q_tasks, purpose="chat.context.pending_alerts_limit_5")
            if not tasks_df.empty:
                context_data["alerts"] = {
                    "count": len(tasks_df),
                    "critical_count": len(tasks_df[tasks_df['priority'] == 'Critical']) if 'priority' in tasks_df.columns else 0,
                    "tasks": tasks_df.to_dict('records'),
                    "formatted": tasks_df[['task_type', 'item_involved', 'description', 'priority']].to_string(index=False)
                }
        except Exception:
            pass

        

        # Enhanced financial summary with trends and insights
        try:
            q_finance = f"""
                SELECT 
                    (SELECT SUM(total_revenue) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_revenue,
                    (SELECT SUM(amount) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_expenses,
                    (SELECT SUM(total_revenue) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) AND bill_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as prev_week_revenue,
                    (SELECT SUM(amount) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY) AND expense_date < DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as prev_week_expenses,
                    (SELECT COUNT(DISTINCT bill_date) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as active_days,
                    (SELECT AVG(total_revenue) FROM (SELECT bill_date, SUM(total_revenue) as total_revenue FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY) GROUP BY bill_date)) as avg_daily_revenue_30d
            """
            
            fin_df, _ = query_to_df(client, settings, q_finance, purpose="chat.context.financial_summary_7d")
            
            if not fin_df.empty and fin_df.iloc[0]['week_revenue']:
                rev = float(fin_df.iloc[0]['week_revenue'] or 0)
                exp = float(fin_df.iloc[0]['week_expenses'] or 0)
                prev_rev = float(fin_df.iloc[0].get('prev_week_revenue') or 0)
                prev_exp = float(fin_df.iloc[0].get('prev_week_expenses') or 0)
                active_days = int(fin_df.iloc[0].get('active_days') or 0)
                avg_daily_30d = float(fin_df.iloc[0].get('avg_daily_revenue_30d') or 0)
                
                delta_rev = rev - prev_rev
                delta_exp = exp - prev_exp
                pct_rev = (delta_rev / prev_rev * 100) if prev_rev > 0 else None
                pct_exp = (delta_exp / prev_exp * 100) if prev_exp > 0 else None
                
                # Calculate performance vs 30-day average
                current_daily_avg = rev / max(active_days, 1)
                performance_vs_avg = ((current_daily_avg - avg_daily_30d) / avg_daily_30d * 100) if avg_daily_30d > 0 else None
                
                context_data["financial_summary"] = {
                    "week_revenue": rev,
                    "week_expenses": exp,
                    "net_profit": rev - exp,
                    "revenue_change": delta_rev,
                    "revenue_change_pct": pct_rev,
                    "expense_change": delta_exp,
                    "expense_change_pct": pct_exp,
                    "profit_margin": (rev - exp) / rev * 100 if rev > 0 else 0,
                    "performance_vs_30d_avg": performance_vs_avg,
                    "active_days": active_days,
                    "formatted": f"Financial Summary (Last 7 days): Revenue: ₹{rev:,.2f}, Expenses: ₹{exp:,.2f}, Net: ₹{rev-exp:,.2f}\nΔ vs Previous Week: Revenue {delta_rev:+,.2f} ({pct_rev:+.1f}% if pct_rev else 'N/A'), Expenses {delta_exp:+,.2f} ({pct_exp:+.1f}% if pct_exp else 'N/A')\nProfit Margin: {(rev-exp)/rev*100 if rev > 0 else 0:.1f}%"
                }
        except Exception:
            pass

            
    except Exception as e:
        print(f"Error getting enhanced context: {e}")
    
    return context_data


def get_bigquery_context(client, settings, limit=10):
    """Backward compatibility function - returns old format"""
    enhanced_data = get_enhanced_bigquery_context(client, settings, "", limit)
    
    context_parts = []
    if enhanced_data.get("sales_data") and enhanced_data["sales_data"].get("formatted"):
        data_type = enhanced_data["sales_data"].get("type", "unknown")
        record_count = enhanced_data["sales_data"].get("records", 0)
        context_parts.append(f"Recent Sales Data ({record_count} {data_type} records):\n{enhanced_data['sales_data']['formatted']}")
    
    if enhanced_data.get("alerts") and enhanced_data["alerts"].get("formatted"):
        alert_count = enhanced_data["alerts"].get("count", 0)
        critical_count = enhanced_data["alerts"].get("critical_count", 0)
        context_parts.append(f"Recent Alerts ({alert_count} total, {critical_count} critical):\n{enhanced_data['alerts']['formatted']}")
    
    if enhanced_data.get("financial_summary") and enhanced_data["financial_summary"].get("formatted"):
        context_parts.append(enhanced_data["financial_summary"]["formatted"])
    
    if enhanced_data.get("learned_patterns"):
        context_parts.append(enhanced_data["learned_patterns"])
    
    return "\n\n".join(context_parts)



def save_conversation_with_learning(client, settings, user_message: str, ai_response: str, 
                                  response_time_ms: int = 0, rating: Optional[int] = None, 
                                  feedback: Optional[str] = None, query_type: str = "general") -> str:
    """Enhanced conversation saving with Evolution Core learning integration"""
    interaction_id = ""
    
    try:
        # Fix encoding for Windows
        if sys.platform == 'win32':
            try:
                user_message = user_message.encode('utf-8', errors='replace').decode('utf-8')
                ai_response = ai_response.encode('utf-8', errors='replace').decode('utf-8')
            except:
                pass

        
        # Enhanced conversation data with metadata
        conversation_data = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message[:5000] if len(user_message) > 5000 else user_message,
            'ai_response': ai_response[:10000] if len(ai_response) > 10000 else ai_response,
            'response_time_ms': response_time_ms,
            'query_type': query_type,
            'message_length': len(user_message),
            'response_length': len(ai_response)
        }

        # Enhanced chat memory table with metadata
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory_enhanced"
        
        try:
            client.get_table(table_id)
        except NotFound:
            # Create enhanced table schema
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
                bigquery.SchemaField("user_message", "STRING"),
                bigquery.SchemaField("ai_response", "STRING"),
                bigquery.SchemaField("response_time_ms", "INT64"),
                bigquery.SchemaField("query_type", "STRING"),
                bigquery.SchemaField("message_length", "INT64"),
                bigquery.SchemaField("response_length", "INT64"),
                bigquery.SchemaField("interaction_id", "STRING")
            ]
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)

        
        # Generate interaction ID
        import hashlib
        interaction_id = hashlib.md5(
            f"{datetime.now().isoformat()}:{user_message[:100]}".encode()
        ).hexdigest()[:16]
        
        conversation_data['interaction_id'] = interaction_id
        
        # Insert conversation with enhanced data
        try:
            errors = client.insert_rows_json(table_id, [conversation_data])
            if errors:
                print(f"Error saving enhanced conversation: {errors}")
            else:
                # Integrate with Evolution Core for learning
                if EvolutionCore:
                    try:
                        evolution = EvolutionCore()
                        evolution.record_interaction(
                            user_query=user_message,
                            ai_response=ai_response,
                            query_type=query_type,
                            response_time_ms=response_time_ms,
                            rating=rating,
                            feedback=feedback
                        )
                    except Exception as e:
                        print(f"Evolution Core learning error: {e}")
        except Exception as e:
            # Fallback to basic table format
            try:
                basic_table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory"
                basic_data = {
                    'timestamp': conversation_data['timestamp'],
                    'user_message': conversation_data['user_message'],
                    'ai_response': conversation_data['ai_response']
                }
                client.insert_rows_json(basic_table_id, [basic_data])
            except:
                pass

        return interaction_id
        
    except Exception as e:
        # Don't fail chat if save fails
        import traceback
        print(f"Error in save_conversation_with_learning: {e}")
        traceback.print_exc()
        return ""


def save_conversation(client, settings, user_message, ai_response):
    """Backward compatibility function"""
    return save_conversation_with_learning(client, settings, user_message, ai_response)



def get_enhanced_conversation_history(client, settings, limit=10) -> List[Dict[str, Any]]:
    """Get enhanced conversation history with metadata"""
    try:
        # Try enhanced table first
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory_enhanced"
        q = f"""
            SELECT user_message, ai_response, timestamp, query_type, response_time_ms, interaction_id
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        df = client.query(q).to_dataframe()
        if not df.empty:
            return df.to_dict('records')
    except Exception:
        pass
    
    # Fallback to basic table
    try:
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory"

        q = f"""
            SELECT user_message, ai_response, timestamp
            FROM `{table_id}`
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        df = client.query(q).to_dataframe()
        return df.to_dict('records') if not df.empty else []
    except Exception:
        return []


def get_conversation_history(client, settings, limit=10):
    """Backward compatibility function"""
    return get_enhanced_conversation_history(client, settings, limit)



def chat_with_titan_intelligence(client, settings, user_message: str, 
                                conversation_history: Optional[List] = None,
                                query_type: str = "general",
                                use_forensic_mode: bool = False) -> Dict[str, Any]:
    """
    TITAN Advanced AI Chat with Forensic-Grade Intelligence
    
    Features:
    - Deep Context Injection with pre-queries
    - Natural English → SQL → Perfect Output
    - Structured, Exportable Answers
    - Self-Improvement through Evolution Core
    - Phoenix Protocol error recovery
    """
    import time
    start_time = time.time()
    
    try:
        # Initialize Phoenix Protocols for self-healing
        phoenix = None
        if PhoenixProtocols:
            try:
                phoenix = PhoenixProtocols()
            except Exception:
                pass
        
        # Get enhanced context with learning integration
        context_data = get_enhanced_bigquery_context(client, settings, user_message, limit=15)
        
        if use_forensic_mode:
            # Forensic mode: Run pre-queries for exact figures
            forensic_context = _run_forensic_pre_queries(client, settings, user_message)
            context_data["forensic_data"] = forensic_context
        
        # Build advanced TITAN prompt
        system_prompt = _build_titan_system_prompt(context_data, use_forensic_mode)
        
        # Add conversation history
        history_text = ""
        if conversation_history:
            for conv in conversation_history[-3:]:
                user_msg = conv.get('user_message', '')
                ai_msg = conv.get('ai_response', '')
                if user_msg and ai_msg:
                    history_text += f"User: {user_msg[:200]}...\n"
                    history_text += f"TITAN: {ai_msg[:300]}...\n\n"
        
        full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nTITAN:"
        
        # Call Gemini with enhanced configuration
        response_text = _call_gemini_advanced(settings, full_prompt, query_type)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save with learning integration
        interaction_id = save_conversation_with_learning(
            client, settings, user_message, response_text, 
            response_time_ms=response_time_ms, query_type=query_type
        )
        
        return {
            "response": response_text,
            "interaction_id": interaction_id,
            "response_time_ms": response_time_ms,
            "context_used": bool(context_data.get("sales_data") or context_data.get("financial_summary")),
            "forensic_mode": use_forensic_mode,
            "learning_applied": bool(context_data.get("learned_patterns")),
            "alerts_count": context_data.get("alerts", {}).get("count", 0)
        }
        
    except Exception as e:
        # Phoenix Protocol: Self-healing attempt
        if phoenix:
            try:
                healing_result = phoenix.heal_function(
                    func=chat_with_titan_intelligence,
                    error=e,
                    args=(client, settings, user_message),
                    kwargs={"conversation_history": conversation_history, "query_type": query_type}
                )
                if healing_result.status.value == "healed":
                    print(f"🔥 Phoenix Protocol: Auto-healed chat error - {healing_result.fix_description}")
            except Exception:
                pass
        
        # Fallback to basic response
        return {
            "response": f"I encountered an issue: {str(e)}. Let me try a different approach.",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000)
        }


def _run_forensic_pre_queries(client, settings, user_message: str) -> Dict[str, Any]:
    """Run pre-queries for forensic-grade exact figures"""
    forensic_data = {}
    
    try:
        # Detect query intent and run relevant pre-queries
        msg_lower = user_message.lower()
        
        if any(word in msg_lower for word in ['expense', 'cost', 'spend', 'payment']):
            # Expense investigator pre-query
            q_exp_detail = f"""
                SELECT 
                    ledger_category,
                    sub_category,
                    employee,
                    paid_from,
                    SUM(amount) as total_amount,
                    COUNT(*) as transaction_count,
                    AVG(amount) as avg_amount,
                    DATE(MAX(expense_date)) as latest_date
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master`
                WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY ledger_category, sub_category, employee, paid_from
                ORDER BY total_amount DESC
                LIMIT 20
            """
            
            try:
                from utils.bq_guardrails import query_to_df
                exp_df, _ = query_to_df(client, settings, q_exp_detail, purpose="forensic.expense_detail")
                if not exp_df.empty:
                    forensic_data["expense_breakdown"] = exp_df.to_dict('records')
            except Exception:
                pass
        
        if any(word in msg_lower for word in ['revenue', 'sales', 'income', 'profit']):
            # Revenue forensics
            q_rev_detail = f"""
                SELECT 
                    DATE(bill_date) as sale_date,
                    order_type,
                    payment_mode,
                    delivery_partner,
                    SUM(total_revenue) as daily_revenue,
                    COUNT(DISTINCT order_id) as orders,
                    AVG(total_revenue) as avg_order_value
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed`
                WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
                GROUP BY DATE(bill_date), order_type, payment_mode, delivery_partner
                ORDER BY sale_date DESC, daily_revenue DESC
                LIMIT 50
            """
            
            try:
                from utils.bq_guardrails import query_to_df
                rev_df, _ = query_to_df(client, settings, q_rev_detail, purpose="forensic.revenue_detail")
                if not rev_df.empty:
                    forensic_data["revenue_breakdown"] = rev_df.to_dict('records')
            except Exception:
                pass
    
    except Exception:
        pass
    
    return forensic_data


def _build_titan_system_prompt(context_data: Dict[str, Any], use_forensic_mode: bool = False) -> str:
    """Build advanced TITAN system prompt with intelligence context"""
    
    mode_description = "Forensic-Grade Business Intelligence" if use_forensic_mode else "Advanced Business Intelligence"
    
    prompt_parts = [
        f"You are TITAN, the world's most advanced AI business assistant with {mode_description}.",
        "\n🏢 **CAFE MELLOW COMMAND CENTER** | Tiruppur, Tamil Nadu, India",
        "\n**TITAN Capabilities:**",
        "• Forensic-grade expense and business intelligence",
        "• Deep Context Injection with real BigQuery data",
        "• Natural English → SQL → Perfect Output", 
        "• Self-learning and pattern recognition",
        "• Structured, exportable answers (Tables → Analysis → Context)",
        "• Phoenix Protocol self-healing technology",
        "\n**Response Protocol:**",
        "1. **TABLES FIRST** - Always lead with raw fact tables, then analysis",
        "2. **EXACT FIGURES** - Use precise numbers from data, never estimates", 
        "3. **TREND ANALYSIS** - Compare with historical data and market context",
        "4. **ACTIONABLE INSIGHTS** - Provide specific recommendations",
        "5. **TIRUPPUR CONTEXT** - Include local market and operational context",
        "\n**Available Real-Time Data:**"
    ]
    
    if context_data.get("sales_data"):
        sales_info = context_data["sales_data"]
        prompt_parts.append(f"\n📊 **Sales Data**: {sales_info.get('records', 0)} recent {sales_info.get('type', 'unknown')} records")
    
    if context_data.get("financial_summary"):
        fin_data = context_data["financial_summary"]
        prompt_parts.append(f"\n💰 **Financial Summary**: ₹{fin_data.get('week_revenue', 0):,.2f} revenue, ₹{fin_data.get('net_profit', 0):,.2f} profit")
    
    if context_data.get("alerts"):
        alert_info = context_data["alerts"]
        critical_count = alert_info.get("critical_count", 0)
        total_count = alert_info.get("count", 0)
        status = "🔴 CRITICAL ALERTS" if critical_count > 0 else "🟡 Active Alerts"
        prompt_parts.append(f"\n🚨 **{status}**: {total_count} total ({critical_count} critical)")
    
    if context_data.get("learned_patterns"):
        prompt_parts.append(f"\n🧠 **Applied Learning**: {len(context_data['learned_patterns'].split('\n'))} learned strategies active")
    
    if use_forensic_mode and context_data.get("forensic_data"):
        forensic = context_data["forensic_data"]
        prompt_parts.append("\n🔍 **FORENSIC MODE ACTIVE** - Deep pre-query data loaded")
        if forensic.get("expense_breakdown"):
            prompt_parts.append(f"   • Expense forensics: {len(forensic['expense_breakdown'])} detailed breakdowns")
        if forensic.get("revenue_breakdown"):
            prompt_parts.append(f"   • Revenue forensics: {len(forensic['revenue_breakdown'])} detailed breakdowns")
    
    prompt_parts.extend([
        "\n**Context Data:**",
        f"{context_data.get('sales_data', {}).get('formatted', 'No recent sales data')}",
        f"\n{context_data.get('financial_summary', {}).get('formatted', '')}",
        f"\n{context_data.get('alerts', {}).get('formatted', '')}"
    ])
    
    if context_data.get("learned_patterns"):
        prompt_parts.append(f"\n{context_data['learned_patterns']}")
    
    prompt_parts.extend([
        "\n**RESPONSE FORMAT:**",
        "1. 📋 **TABLES** (Raw data with exact figures)",
        "2. 📈 **TREND ANALYSIS** (Patterns and comparisons)", 
        "3. 🎯 **TIRUPPUR CONTEXT** (Local market insights)",
        "4. ⚡ **ACTION ITEMS** (Specific recommendations)",
        "\n**Remember**: Table-first approach, exact figures only, suggest Evolution Lab improvements when needed."
    ])
    
    return "\n".join(prompt_parts)


def _call_gemini_advanced(settings, prompt: str, query_type: str) -> str:
    """Enhanced Gemini API call with advanced configuration"""
    try:
        url = f"{settings.GEMINI_URL}?key={settings.GEMINI_API_KEY}"
        
        # Advanced configuration based on query type
        config = {
            "temperature": 0.3 if query_type == "forensic" else 0.7,
            "topK": 20 if query_type == "forensic" else 40,
            "topP": 0.8 if query_type == "forensic" else 0.95,
            "maxOutputTokens": 3072,
            "candidateCount": 1
        }
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": config
        }
        
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if parts and 'text' in parts[0]:
                        return parts[0]['text']
            
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                return f"TITAN encountered an API issue: {error_msg}. Please try rephrasing your question."
        
        return "TITAN is temporarily experiencing technical difficulties. Please try again."
        
    except Exception as e:
        return f"TITAN system error: {str(e)}. Attempting self-repair..."


def chat_with_gemini(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Backward compatibility function with enhanced capabilities"""
    if not use_enhanced_prompt:
        # Use new TITAN intelligence system
        result = chat_with_titan_intelligence(client, settings, user_message, conversation_history)
        return result.get("response", "TITAN is initializing...")
    
    _save_user = (original_user_prompt or user_message) if use_enhanced_prompt else user_message

    try:
        if use_enhanced_prompt:
            full_prompt = user_message + "\n\nAssistant:"

        else:
            # Get BigQuery context
            context = get_bigquery_context(client, settings)
            
            # Build enhanced system prompt
            system_prompt = f"""You are TITAN, the world's most advanced AI business assistant for Cafe Mellow in Tiruppur, Tamil Nadu, India.

Your personality:
- Think and respond like a top-tier business consultant
- Be conversational and human-like, not robotic
- Provide deep insights, not just numbers
- Be proactive and strategic
- Use natural language with personality

Available Business Data:
{context}

Business Location: Tiruppur, Tamil Nadu, India

Instructions:
1. Answer questions naturally and conversationally
2. Provide context and insights, not just data
3. Suggest actions and strategies
4. Compare with market standards when relevant
5. Be specific and actionable
6. Use examples from the actual data
7. Never guess - only use available data or clearly state limitations

Remember: You're a trusted advisor, not just a data reporter."""

            # Build conversation history
            history_text = ""
            if conversation_history:
                for conv in conversation_history[-5:]:
                    user_msg = conv.get('user_message', '')
                    ai_msg = conv.get('ai_response', '')
                    if user_msg and ai_msg:
                        history_text += f"User: {user_msg}\n"
                        history_text += f"Assistant: {ai_msg}\n\n"
            
            full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"
        
        # Call Gemini API with proper error handling
        url = f"{settings.GEMINI_URL}?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": full_prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "candidateCount": 1
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response structures
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                
                # Check for content block
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if parts and len(parts) > 0 and 'text' in parts[0]:
                        ai_response = parts[0]['text']
                        
                        # Save conversation only if successful
                        try:
                            save_conversation(client, settings, _save_user, ai_response)
                        except:
                            pass  # Don't fail if save fails
                        
                        return ai_response
                
                # Fallback: try to extract text directly
                if 'text' in candidate:
                    ai_response = candidate['text']
                    try:
                        save_conversation(client, settings, _save_user, ai_response)
                    except:
                        pass
                    return ai_response
            
            # Check for error in response
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                return f"I encountered an issue: {error_msg}. Please try rephrasing your question."
            
            return "I apologize, but I couldn't generate a proper response. The API response format was unexpected. Please try again."
            
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Invalid request')
                return f"Request error: {error_msg}. Please check your question format."
            except:
                return "Invalid request. Please try rephrasing your question."
        elif response.status_code == 401:
            return "Authentication error. Please check your Gemini API key in settings.py"
        elif response.status_code == 429:
            return "Rate limit exceeded. Please wait a moment and try again."
        else:
            return f"API error (Status {response.status_code}): {response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "The request took too long. This might be due to a large query. Please try a simpler question or try again."
    except requests.exceptions.ConnectionError:
        return "Connection error. Please check your internet connection and try again."
    except json.JSONDecodeError as e:
        return f"Error parsing API response. Please try again."
    except Exception as e:
        error_detail = str(e)
        return f"Unexpected error: {error_detail}. Please check the logs for details."




def chat_with_gemini_stream(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Stream Gemini response chunks with TITAN intelligence"""

                    try:

                        save_conversation(client, settings, _save_user, ai_response)

                    except:

                        pass

                    return ai_response

            

            # Check for error in response

            if 'error' in data:

                error_msg = data['error'].get('message', 'Unknown error')

                return f"I encountered an issue: {error_msg}. Please try rephrasing your question."

            

            return "I apologize, but I couldn't generate a proper response. The API response format was unexpected. Please try again."

            

        elif response.status_code == 400:

            try:

                error_data = response.json()

                error_msg = error_data.get('error', {}).get('message', 'Invalid request')

                return f"Request error: {error_msg}. Please check your question format."

            except:

                return "Invalid request. Please try rephrasing your question."

        elif response.status_code == 401:

            return "Authentication error. Please check your Gemini API key in settings.py"

        elif response.status_code == 429:

            return "Rate limit exceeded. Please wait a moment and try again."

        else:

            return f"API error (Status {response.status_code}): {response.text[:200]}"

            

    except requests.exceptions.Timeout:

        return "The request took too long. This might be due to a large query. Please try a simpler question or try again."

    except requests.exceptions.ConnectionError:

        return "Connection error. Please check your internet connection and try again."

    except json.JSONDecodeError as e:

        return f"Error parsing API response. Please try again."

    except Exception as e:

        error_detail = str(e)

        return f"Unexpected error: {error_detail}. Please check the logs for details."





def chat_with_gemini_stream(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):

    """Stream Gemini response chunks.



    Yields incremental text segments as they arrive from Gemini.

    Also saves the full conversation to BigQuery at the end (best-effort).

    """



    _save_user = (original_user_prompt or user_message) if use_enhanced_prompt else user_message



    if use_enhanced_prompt:

        full_prompt = user_message + "\n\nAssistant:"

    else:

        msg_trim = (user_message or "").strip().lower()

        # Fast path: for tiny greetings, don't run multiple BigQuery queries.

        if msg_trim in ("hi", "hello", "hey", "hai", "namaste") or len(msg_trim) <= 4:

            context = "(No BigQuery context loaded for this short greeting.)"

        else:

            context = get_bigquery_context(client, settings)



        system_prompt = f"""You are TITAN, the world's most advanced AI business assistant for Cafe Mellow in Tiruppur, Tamil Nadu, India.



Your personality:

- Think and respond like a top-tier business consultant

- Be conversational and human-like, not robotic

- Provide deep insights, not just numbers

- Be proactive and strategic

- Use natural language with personality



Available Business Data:

{context}



Business Location: Tiruppur, Tamil Nadu, India



Instructions:

1. Answer questions naturally and conversationally

2. Provide context and insights, not just data

3. Suggest actions and strategies

4. Compare with market standards when relevant

5. Be specific and actionable

6. Use examples from the actual data

7. Never guess - only use available data or clearly state limitations



Remember: You're a trusted advisor, not just a data reporter."""



        history_text = ""

        if conversation_history:

            for conv in conversation_history[-5:]:

                user_msg = conv.get("user_message", "")

                ai_msg = conv.get("ai_response", "")

                if user_msg and ai_msg:

                    history_text += f"User: {user_msg}\n"

                    history_text += f"Assistant: {ai_msg}\n\n"



        full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"



    base_url = getattr(settings, "GEMINI_URL", "")

    if not base_url:

        raise RuntimeError("GEMINI_URL is missing")



    # Convert :generateContent to :streamGenerateContent if needed.

    stream_base = base_url.replace(":generateContent", ":streamGenerateContent")

    # Request SSE explicitly so tokens arrive incrementally.

    url = f"{stream_base}?key={settings.GEMINI_API_KEY}&alt=sse"



    payload = {

        "contents": [

            {

                "parts": [

                    {

                        "text": full_prompt,

                    }

                ]

            }

        ],

        "generationConfig": {

            "temperature": 0.9,

            "topK": 40,

            "topP": 0.95,

            "maxOutputTokens": 2048,

            "candidateCount": 1,

        },

    }



    full_text = ""

    try:

        response = requests.post(

            url,

            json=payload,

            timeout=(10, 120),

            stream=True,

            headers={"Accept": "text/event-stream"},

        )

        response.raise_for_status()



        for raw in response.iter_lines(decode_unicode=True):

            if not raw:

                continue



            line = raw.strip()

            if line.startswith("data:"):

                line = line[5:].lstrip()



            # Some implementations may send a terminal marker.

            if line in ("[DONE]", "DONE"):

                break



            try:

                data = json.loads(line)

            except Exception:

                continue



            candidates = data.get("candidates") or []

            if not candidates:

                continue



            content = candidates[0].get("content") or {}

            parts = content.get("parts") or []

            if not parts:

                continue



            text = parts[0].get("text")

            if not text:

                continue



            full_text += text

            yield text



    finally:

        if full_text:

            try:

                save_conversation(client, settings, _save_user, full_text)

            except:

                pass

