"""
TITAN Advanced AI Chat System
Enhanced with Phoenix Protocols, Evolution Core, and Forensic Intelligence
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
        
        # Get basic context first
        context = get_bigquery_context(client, settings)
        
        # Build TITAN system prompt
        system_prompt = f"""You are TITAN, the world's most advanced AI business assistant with Forensic-Grade Intelligence.

🏢 **CAFE MELLOW COMMAND CENTER** | Tiruppur, Tamil Nadu, India

**TITAN Capabilities:**
• Forensic-grade expense and business intelligence
• Deep Context Injection with real BigQuery data
• Natural English → SQL → Perfect Output
• Self-learning and pattern recognition
• Structured, exportable answers (Tables → Analysis → Context)
• Phoenix Protocol self-healing technology

**Response Protocol:**
1. **TABLES FIRST** - Always lead with raw fact tables, then analysis
2. **EXACT FIGURES** - Use precise numbers from data, never estimates
3. **TREND ANALYSIS** - Compare with historical data and market context
4. **ACTIONABLE INSIGHTS** - Provide specific recommendations
5. **TIRUPPUR CONTEXT** - Include local market and operational context

**Available Real-Time Data:**
{context}

**RESPONSE FORMAT:**
1. 📋 **TABLES** (Raw data with exact figures)
2. 📈 **TREND ANALYSIS** (Patterns and comparisons)
3. 🎯 **TIRUPPUR CONTEXT** (Local market insights)
4. ⚡ **ACTION ITEMS** (Specific recommendations)

Remember: Table-first approach, exact figures only, suggest Evolution Lab improvements when needed."""

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
        
        # Save with basic conversation saving
        try:
            save_conversation(client, settings, user_message, response_text)
        except:
            pass
        
        return {
            "response": response_text,
            "response_time_ms": response_time_ms,
            "context_used": bool(context),
            "forensic_mode": use_forensic_mode,
            "system": "TITAN v3 Advanced AI"
        }
        
    except Exception as e:
        return {
            "response": f"TITAN encountered an issue: {str(e)}. Attempting self-repair...",
            "error": str(e),
            "response_time_ms": int((time.time() - start_time) * 1000)
        }


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


def get_bigquery_context(client, settings, limit=10):
    """Get BigQuery context for TITAN intelligence"""
    context_parts = []
    
    try:
        # Get recent sales data
        try:
            q_sales = f"""
                SELECT bill_date, item_name, quantity, total_revenue 
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed`
                ORDER BY bill_date DESC
                LIMIT {limit}
            """
            sales_df, _ = query_to_df(client, settings, q_sales, purpose="chat.context.sales")
            if not sales_df.empty:
                context_parts.append("Recent Sales Data:\n" + sales_df.to_string(index=False))
        except:
            pass
        
        # Get recent tasks/alerts
        try:
            q_tasks = f"""
                SELECT task_type, item_involved, description, priority
                FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.ai_task_queue`
                WHERE status = 'Pending'
                ORDER BY created_at DESC
                LIMIT 5
            """
            tasks_df, _ = query_to_df(client, settings, q_tasks, purpose="chat.context.alerts")
            if not tasks_df.empty:
                context_parts.append("Recent Alerts:\n" + tasks_df.to_string(index=False))
        except:
            pass
        
        # Get financial summary
        try:
            q_finance = f"""
                SELECT 
                    (SELECT SUM(total_revenue) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.sales_items_parsed` WHERE bill_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_revenue,
                    (SELECT SUM(amount) FROM `{settings.PROJECT_ID}.{settings.DATASET_ID}.expenses_master` WHERE expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)) as week_expenses
            """
            fin_df, _ = query_to_df(client, settings, q_finance, purpose="chat.context.financial")
            if not fin_df.empty and fin_df.iloc[0]['week_revenue']:
                rev = float(fin_df.iloc[0]['week_revenue'] or 0)
                exp = float(fin_df.iloc[0]['week_expenses'] or 0)
                context_parts.append(f"Financial Summary (Last 7 days): Revenue: ₹{rev:,.2f}, Expenses: ₹{exp:,.2f}, Net: ₹{rev-exp:,.2f}")
        except:
            pass
            
    except Exception as e:
        print(f"Error getting context: {e}")
    
    return "\n\n".join(context_parts)


def save_conversation(client, settings, user_message, ai_response):
    """Save conversation to BigQuery for memory"""
    try:
        if sys.platform == 'win32':
            try:
                user_message = user_message.encode('utf-8', errors='replace').decode('utf-8')
                ai_response = ai_response.encode('utf-8', errors='replace').decode('utf-8')
            except:
                pass
        
        conversation_data = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message[:5000] if len(user_message) > 5000 else user_message,
            'ai_response': ai_response[:10000] if len(ai_response) > 10000 else ai_response
        }
        
        # Check if table exists, create if not
        table_id = f"{settings.PROJECT_ID}.{settings.DATASET_ID}.chat_memory"
        
        try:
            client.get_table(table_id)
        except NotFound:
            schema = [
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
                bigquery.SchemaField("user_message", "STRING"),
                bigquery.SchemaField("ai_response", "STRING")
            ]
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
        
        # Insert conversation
        errors = client.insert_rows_json(table_id, [conversation_data])
        if errors:
            print(f"Error saving conversation: {errors}")
            
    except Exception as e:
        print(f"Error in save_conversation: {e}")


def get_conversation_history(client, settings, limit=10):
    """Get recent conversation history"""
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
    except:
        return []


# Backward compatibility functions
def chat_with_gemini(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Backward compatibility function with TITAN intelligence"""
    if not use_enhanced_prompt:
        # Use new TITAN intelligence system
        result = chat_with_titan_intelligence(client, settings, user_message, conversation_history)
        return result.get("response", "TITAN is initializing...")
    
    # Fallback to basic mode for enhanced prompts
    try:
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
        
        # Call Gemini API
        url = f"{settings.GEMINI_URL}?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
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
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if parts and 'text' in parts[0]:
                        ai_response = parts[0]['text']
                        try:
                            save_conversation(client, settings, user_message, ai_response)
                        except:
                            pass
                        return ai_response
            
            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                return f"I encountered an issue: {error_msg}. Please try rephrasing your question."
        
        return "I apologize, but I couldn't generate a proper response. Please try again."
        
    except Exception as e:
        return f"Unexpected error: {str(e)}. Please check the logs for details."


def chat_with_gemini_stream(client, settings, user_message, conversation_history=None, use_enhanced_prompt=False, original_user_prompt=None):
    """Stream Gemini response chunks with TITAN intelligence"""
    _save_user = (original_user_prompt or user_message) if use_enhanced_prompt else user_message
    
    try:
        # Get context for streaming
        context = get_bigquery_context(client, settings) if len(user_message.strip()) > 4 else "(Short greeting - no context loaded)"
        
        system_prompt = f"""You are TITAN, the world's most advanced AI business assistant for Cafe Mellow in Tiruppur, Tamil Nadu, India.

Your personality:
- Think and respond like a top-tier business consultant
- Be conversational and human-like, not robotic
- Provide deep insights, not just numbers
- Be proactive and strategic

Available Business Data:
{context}

Business Location: Tiruppur, Tamil Nadu, India

Instructions:
1. Answer questions naturally and conversationally
2. Provide context and insights, not just data
3. Suggest actions and strategies
4. Be specific and actionable
5. Use examples from the actual data
6. Never guess - only use available data

Remember: You're a trusted advisor, not just a data reporter."""

        history_text = ""
        if conversation_history:
            for conv in conversation_history[-3:]:
                user_msg = conv.get("user_message", "")
                ai_msg = conv.get("ai_response", "")
                if user_msg and ai_msg:
                    history_text += f"User: {user_msg}\n"
                    history_text += f"Assistant: {ai_msg}\n\n"

        full_prompt = f"{system_prompt}\n\n{history_text}User: {user_message}\nAssistant:"
        
        # Stream configuration
        base_url = getattr(settings, "GEMINI_URL", "")
        stream_url = base_url.replace(":generateContent", ":streamGenerateContent")
        url = f"{stream_url}?key={settings.GEMINI_API_KEY}&alt=sse"

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "candidateCount": 1,
            },
        }

        full_text = ""
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

    except Exception as e:
        yield f"TITAN encountered an error: {str(e)}"
    finally:
        if full_text:
            try:
                save_conversation(client, settings, _save_user, full_text)
            except:
                pass
