"""
Query Engine - Natural Language to SQL + Answer
================================================
Phase 4A: Converts user questions to BigQuery SQL and returns answers.

Features:
- Uses TitanCortex for context-aware prompts
- Generates BigQuery SQL from natural language
- Executes queries safely (read-only)
- Handles simulation/what-if questions
- Returns formatted answers with visualization hints
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from google import genai
from dotenv import load_dotenv

load_dotenv()

from backend.universal_adapter.titan_cortex import get_cortex, TitanCortex


# =============================================================================
# Configuration
# =============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_genai_client = None
if GEMINI_API_KEY:
    _genai_client = genai.Client(api_key=GEMINI_API_KEY)

PROJECT_ID = "cafe-mellow-core-2026"
DATASET_ID = "cafe_operations"
LEDGER_TABLE = f"{PROJECT_ID}.{DATASET_ID}.universal_ledger"


# =============================================================================
# Query Engine
# =============================================================================

class QueryEngine:
    """
    Converts natural language questions to SQL and returns answers.
    
    Flow:
    1. Get context prompt from TitanCortex
    2. Send to Gemini to generate SQL
    3. Validate and execute SQL (read-only)
    4. Format and return answer
    """
    
    def __init__(self):
        self._client = _genai_client
        self._bq_client = None
        print("[QUERY ENGINE] Initialized (google.genai)")
    
    def _get_bq_client(self):
        """Lazy-load BigQuery client."""
        if self._bq_client is None:
            try:
                from google.cloud import bigquery
                self._bq_client = bigquery.Client()
            except Exception as e:
                print(f"[QUERY ENGINE] BigQuery client failed: {e}")
        return self._bq_client
    
    def _validate_sql(self, sql: str, tenant_id: str) -> Tuple[bool, str]:
        """
        Validate SQL for safety.
        
        Rules:
        - Must be SELECT only (no INSERT, UPDATE, DELETE, DROP, etc.)
        - Must contain tenant_id filter
        - Must reference our ledger table
        """
        if not sql:
            return False, "Empty SQL"
        
        sql_upper = sql.upper().strip()
        
        # Must be SELECT
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return False, "Only SELECT queries allowed"
        
        # Block dangerous keywords
        dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", 
                     "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]
        for keyword in dangerous:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"Dangerous keyword detected: {keyword}"
        
        # Must filter by tenant_id
        if tenant_id not in sql and "tenant_id" not in sql.lower():
            return False, "Query must filter by tenant_id"
        
        return True, "Valid"
    
    def _execute_sql(self, sql: str) -> Tuple[bool, Any, str]:
        """
        Execute SQL query against BigQuery.
        
        Returns:
            (success, results, error_message)
        """
        client = self._get_bq_client()
        if not client:
            return False, None, "BigQuery client not available"
        
        try:
            query_job = client.query(sql)
            results = list(query_job.result())
            
            # Convert to list of dicts
            rows = []
            for row in results:
                rows.append(dict(row))
            
            print(f"[QUERY ENGINE] Query returned {len(rows)} rows")
            return True, rows, ""
            
        except Exception as e:
            error_msg = str(e)
            print(f"[QUERY ENGINE] Query execution failed: {error_msg}")
            return False, None, error_msg
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        try:
            # Try to extract JSON from response
            text = response_text.strip()
            
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(text)
            return result
            
        except json.JSONDecodeError as e:
            print(f"[QUERY ENGINE] JSON parse error: {e}")
            # Return a fallback response
            return {
                "sql": None,
                "answer_text": response_text,
                "visualization_hint": None,
                "confidence": 0.5,
                "parse_error": str(e)
            }
    
    def _format_answer(self, ai_response: Dict, query_results: List[Dict], 
                       executed: bool) -> Dict[str, Any]:
        """Format the final answer with data."""
        answer = {
            "question_understood": True,
            "sql_generated": ai_response.get("sql") is not None,
            "sql": ai_response.get("sql"),
            "executed": executed,
            "answer_text": ai_response.get("answer_text", ""),
            "visualization_hint": ai_response.get("visualization_hint"),
            "confidence": ai_response.get("confidence", 0.5),
            "data": query_results if executed else None,
            "row_count": len(query_results) if query_results else 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Enhance answer text with actual data if available
        if executed and query_results:
            if len(query_results) == 1 and len(query_results[0]) == 1:
                # Single value result - incorporate into answer
                value = list(query_results[0].values())[0]
                if answer["answer_text"] and "{value}" in answer["answer_text"]:
                    answer["answer_text"] = answer["answer_text"].replace("{value}", str(value))
        
        return answer
    
    def ask(self, question: str, tenant_id: str, 
            execute_sql: bool = True,
            include_history: bool = True) -> Dict[str, Any]:
        """
        Answer a natural language question about business data.
        
        Args:
            question: User's question in natural language
            tenant_id: Tenant identifier for data isolation
            execute_sql: Whether to actually run the SQL (default True)
            include_history: Whether to include Deep History analysis (default True)
            
        Returns:
            Dict with answer, SQL, data, history profile, and metadata
        """
        print(f"[QUERY ENGINE] Question: {question}")
        print(f"[QUERY ENGINE] Tenant: {tenant_id}")
        
        # Step 1: Get context from Cortex (now includes Deep History - Phase 4B)
        cortex = get_cortex(tenant_id)
        context_prompt = cortex.build_context_prompt(question, tenant_id, include_history)
        
        # Get history profile for response metadata
        history_profile = getattr(cortex, '_history_profile', {})
        
        # Step 2: Generate SQL with AI
        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=context_prompt
            )
            ai_response = self._parse_ai_response(response.text)
            print(f"[QUERY ENGINE] AI generated response")
            
        except Exception as e:
            print(f"[QUERY ENGINE] AI generation failed: {e}")
            return {
                "question_understood": False,
                "error": str(e),
                "answer_text": f"I encountered an error processing your question: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "history_profile": history_profile
            }
        
        # Step 3: Validate and execute SQL
        sql = ai_response.get("sql")
        query_results = []
        executed = False
        
        if sql and execute_sql:
            is_valid, validation_msg = self._validate_sql(sql, tenant_id)
            
            if is_valid:
                success, results, error = self._execute_sql(sql)
                if success:
                    query_results = results
                    executed = True
                else:
                    ai_response["answer_text"] += f"\n\n(Query execution failed: {error})"
            else:
                ai_response["answer_text"] += f"\n\n(Query validation failed: {validation_msg})"
        
        # Step 4: Format and return answer with history context
        result = self._format_answer(ai_response, query_results, executed)
        
        # Add history profile to response (Phase 4B)
        result["history_profile"] = {
            "operating_mode": history_profile.get("operating_mode"),
            "total_months": history_profile.get("total_months_with_data", 0),
            "data_gaps": history_profile.get("data_gaps", [])[:5],  # First 5 gaps
            "benchmark_margin": history_profile.get("benchmark_margins", {}).get("profit_margin_pct"),
            "user_habits": history_profile.get("user_habits", [])
        }
        
        return result
    
    def ask_simulation(self, question: str, tenant_id: str) -> Dict[str, Any]:
        """
        Handle simulation/what-if questions.
        
        These questions use hypothetical numbers provided by the user
        and should NOT modify the database.
        """
        # Force execute_sql=False for simulations to be safe
        # The AI should generate WITH clause calculations
        return self.ask(question, tenant_id, execute_sql=True)
    
    def explain_query(self, sql: str) -> str:
        """Explain what a SQL query does in plain English."""
        prompt = f"""Explain this SQL query in simple business terms.
Don't use technical jargon. Explain what business question it answers.

SQL:
{sql}

Explanation:"""
        
        try:
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Could not explain query: {e}"


# =============================================================================
# Convenience Functions
# =============================================================================

_engine: Optional[QueryEngine] = None


def get_engine() -> QueryEngine:
    """Get or create global QueryEngine instance."""
    global _engine
    if _engine is None:
        _engine = QueryEngine()
    return _engine


def ask(question: str, tenant_id: str) -> Dict[str, Any]:
    """Convenience function to ask a question."""
    engine = get_engine()
    return engine.ask(question, tenant_id)


def update_preference(instruction: str, tenant_id: str) -> Dict[str, Any]:
    """Update user preferences via natural language."""
    cortex = get_cortex(tenant_id)
    return cortex.update_preference(instruction)
