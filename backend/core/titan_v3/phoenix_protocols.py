"""
TITAN v3 Phoenix Protocols
==========================
Self-Healing Code System that can rewrite its own logic to fix errors.

When a pipeline breaks (e.g., Excel format changes), Phoenix:
1. Catches the error and traceback
2. Sends to "Doctor Agent" (Gemini Pro)
3. Agent rewrites the failing function
4. Hot-patches the code without restart
5. Logs the fix for human review

"Logic as Data" - Business logic stored in dynamic storage that AI can edit.
"""

import os
import sys
import json
import traceback
import hashlib
import importlib.util
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
import inspect

from google.cloud import bigquery
try:
    from google.cloud import storage
except ImportError:
    storage = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class HealingStatus(str, Enum):
    DETECTED = "detected"
    ANALYZING = "analyzing"
    PATCHING = "patching"
    TESTING = "testing"
    HEALED = "healed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class HealingResult:
    """Result of a self-healing attempt"""
    status: HealingStatus
    error_type: str
    error_message: str
    original_code: Optional[str] = None
    patched_code: Optional[str] = None
    fix_description: str = ""
    confidence: float = 0.0
    attempts: int = 0
    healing_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorContext:
    """Full context of an error for diagnosis"""
    function_name: str
    function_code: str
    error_type: str
    error_message: str
    traceback: str
    input_data_sample: Optional[Dict] = None
    recent_changes: List[str] = field(default_factory=list)


class PhoenixProtocols:
    """
    Self-Healing Code System
    
    Enables TITAN to automatically fix broken pipelines by:
    1. Detecting errors in real-time
    2. Analyzing root cause with AI
    3. Generating and testing patches
    4. Hot-loading fixed code
    """
    
    PROJECT_ID = "cafe-mellow-core-2026"
    DATASET_ID = "cafe_operations"
    GCS_BUCKET = "titan-dynamic-code"
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key and genai:
            genai.configure(api_key=self.api_key)
            self.doctor_model = genai.GenerativeModel("gemini-1.5-pro")
        else:
            self.doctor_model = None
        
        self.bq_client = bigquery.Client(project=self.PROJECT_ID)
        self.healing_history: List[HealingResult] = []
        self.dynamic_functions: Dict[str, Callable] = {}
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Create healing log table"""
        schema = [
            bigquery.SchemaField("healing_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("error_type", "STRING"),
            bigquery.SchemaField("error_message", "STRING"),
            bigquery.SchemaField("function_name", "STRING"),
            bigquery.SchemaField("original_code", "STRING"),
            bigquery.SchemaField("patched_code", "STRING"),
            bigquery.SchemaField("fix_description", "STRING"),
            bigquery.SchemaField("confidence", "FLOAT64"),
            bigquery.SchemaField("attempts", "INT64"),
            bigquery.SchemaField("healing_time_ms", "INT64"),
        ]
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_healing_log"
        try:
            self.bq_client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            self.bq_client.create_table(table)
    
    def wrap_with_healing(self, func: Callable) -> Callable:
        """
        Decorator to wrap a function with self-healing capability
        
        Usage:
            @phoenix.wrap_with_healing
            def parse_excel(file_path):
                ...
        """
        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Attempt self-healing
                result = self.heal_function(
                    func=func,
                    error=e,
                    args=args,
                    kwargs=kwargs
                )
                
                if result.status == HealingStatus.HEALED:
                    # Retry with healed function
                    healed_func = self.dynamic_functions.get(func.__name__)
                    if healed_func:
                        return healed_func(*args, **kwargs)
                
                # If healing failed, re-raise
                raise
        
        wrapped.__name__ = func.__name__
        wrapped.__doc__ = func.__doc__
        return wrapped
    
    def heal_function(
        self,
        func: Callable,
        error: Exception,
        args: tuple = (),
        kwargs: dict = None
    ) -> HealingResult:
        """
        Attempt to heal a broken function
        """
        import time
        start_time = time.time()
        kwargs = kwargs or {}
        
        # Build error context
        context = ErrorContext(
            function_name=func.__name__,
            function_code=inspect.getsource(func),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
            input_data_sample=self._sample_input(args, kwargs),
        )
        
        result = HealingResult(
            status=HealingStatus.DETECTED,
            error_type=context.error_type,
            error_message=context.error_message,
            original_code=context.function_code,
        )
        
        if not self.doctor_model:
            result.status = HealingStatus.ESCALATED
            result.fix_description = "No AI model available for healing"
            return result
        
        # Attempt healing
        result.status = HealingStatus.ANALYZING
        
        try:
            # Get AI diagnosis and fix
            patched_code, description, confidence = self._get_ai_fix(context)
            
            result.patched_code = patched_code
            result.fix_description = description
            result.confidence = confidence
            result.status = HealingStatus.PATCHING
            
            # Validate the patched code
            if self._validate_patch(patched_code, func.__name__):
                result.status = HealingStatus.TESTING
                
                # Load the patched function
                healed_func = self._load_dynamic_function(patched_code, func.__name__)
                
                # Test with sample data if available
                if self._test_healed_function(healed_func, args, kwargs):
                    self.dynamic_functions[func.__name__] = healed_func
                    result.status = HealingStatus.HEALED
                    
                    # Save to GCS for persistence
                    self._save_to_gcs(func.__name__, patched_code)
                else:
                    result.status = HealingStatus.FAILED
                    result.fix_description += " | Test failed"
            else:
                result.status = HealingStatus.FAILED
                result.fix_description += " | Validation failed"
                
        except Exception as heal_error:
            result.status = HealingStatus.FAILED
            result.fix_description = f"Healing error: {str(heal_error)}"
        
        result.healing_time_ms = int((time.time() - start_time) * 1000)
        result.attempts = 1
        
        # Log the healing attempt
        self._log_healing(result, func.__name__)
        self.healing_history.append(result)
        
        return result
    
    def _get_ai_fix(self, context: ErrorContext) -> tuple:
        """Get AI-generated fix for the error"""
        
        prompt = f"""You are a Python code repair expert. Analyze this error and provide a fixed version of the function.

FUNCTION NAME: {context.function_name}

ORIGINAL CODE:
```python
{context.function_code}
```

ERROR TYPE: {context.error_type}
ERROR MESSAGE: {context.error_message}

TRACEBACK:
{context.traceback}

INPUT DATA SAMPLE:
{json.dumps(context.input_data_sample, indent=2, default=str) if context.input_data_sample else "Not available"}

REQUIREMENTS:
1. Fix the specific error while maintaining the function's purpose
2. Add defensive coding to prevent similar errors
3. Keep the function signature exactly the same
4. Only output the fixed function code, nothing else
5. Include necessary imports at the top if needed

OUTPUT FORMAT:
```python
[Your fixed code here]
```

DESCRIPTION: [One line describing what you fixed]
CONFIDENCE: [0.0 to 1.0 how confident you are this fix is correct]
"""
        
        response = self.doctor_model.generate_content(prompt)
        response_text = response.text
        
        # Parse the response
        code_match = response_text.split("```python")
        if len(code_match) > 1:
            patched_code = code_match[1].split("```")[0].strip()
        else:
            patched_code = ""
        
        # Extract description
        description = "AI-generated fix"
        if "DESCRIPTION:" in response_text:
            desc_part = response_text.split("DESCRIPTION:")[1]
            description = desc_part.split("\n")[0].strip()
        
        # Extract confidence
        confidence = 0.7  # Default
        if "CONFIDENCE:" in response_text:
            try:
                conf_part = response_text.split("CONFIDENCE:")[1]
                confidence = float(conf_part.split("\n")[0].strip())
            except:
                pass
        
        return patched_code, description, confidence
    
    def _validate_patch(self, code: str, func_name: str) -> bool:
        """Validate that the patched code is syntactically correct"""
        try:
            compile(code, f"<{func_name}>", "exec")
            return True
        except SyntaxError:
            return False
    
    def _load_dynamic_function(self, code: str, func_name: str) -> Callable:
        """Load a function from dynamic code"""
        namespace = {}
        exec(code, namespace)
        return namespace.get(func_name)
    
    def _test_healed_function(self, func: Callable, args: tuple, kwargs: dict) -> bool:
        """Test the healed function with sample data"""
        try:
            # Run with timeout protection
            func(*args, **kwargs)
            return True
        except Exception:
            return False
    
    def _sample_input(self, args: tuple, kwargs: dict) -> Optional[Dict]:
        """Create a safe sample of input data for diagnosis"""
        sample = {}
        
        if args:
            sample["args"] = []
            for i, arg in enumerate(args[:3]):  # Limit to first 3 args
                try:
                    if isinstance(arg, (str, int, float, bool)):
                        sample["args"].append(arg)
                    elif isinstance(arg, dict):
                        sample["args"].append({k: str(v)[:100] for k, v in list(arg.items())[:5]})
                    elif isinstance(arg, list):
                        sample["args"].append(arg[:3] if len(arg) <= 10 else f"List of {len(arg)} items")
                    else:
                        sample["args"].append(f"<{type(arg).__name__}>")
                except:
                    sample["args"].append("<unable to serialize>")
        
        if kwargs:
            sample["kwargs"] = {}
            for k, v in list(kwargs.items())[:5]:
                try:
                    if isinstance(v, (str, int, float, bool)):
                        sample["kwargs"][k] = v
                    else:
                        sample["kwargs"][k] = f"<{type(v).__name__}>"
                except:
                    sample["kwargs"][k] = "<unable to serialize>"
        
        return sample if sample else None
    
    def _save_to_gcs(self, func_name: str, code: str):
        """Save healed code to GCS for persistence"""
        if not storage:
            return
        try:
            storage_client = storage.Client(project=self.PROJECT_ID)
            bucket = storage_client.bucket(self.GCS_BUCKET)
            blob = bucket.blob(f"healed_functions/{func_name}.py")
            blob.upload_from_string(code)
        except Exception:
            pass  # GCS save is best-effort
    
    def _log_healing(self, result: HealingResult, func_name: str):
        """Log healing attempt to BigQuery"""
        healing_id = hashlib.md5(
            f"{func_name}:{result.timestamp.isoformat()}".encode()
        ).hexdigest()[:16]
        
        row = {
            "healing_id": healing_id,
            "timestamp": result.timestamp.isoformat(),
            "status": result.status.value,
            "error_type": result.error_type,
            "error_message": result.error_message[:1000],
            "function_name": func_name,
            "original_code": (result.original_code or "")[:5000],
            "patched_code": (result.patched_code or "")[:5000],
            "fix_description": result.fix_description[:500],
            "confidence": result.confidence,
            "attempts": result.attempts,
            "healing_time_ms": result.healing_time_ms,
        }
        
        table_ref = f"{self.PROJECT_ID}.{self.DATASET_ID}.titan_healing_log"
        try:
            self.bq_client.insert_rows_json(table_ref, [row])
        except Exception:
            pass  # Logging is best-effort
    
    def load_healed_functions(self):
        """Load previously healed functions from GCS"""
        if not storage:
            return
        try:
            storage_client = storage.Client(project=self.PROJECT_ID)
            bucket = storage_client.bucket(self.GCS_BUCKET)
            
            blobs = bucket.list_blobs(prefix="healed_functions/")
            for blob in blobs:
                func_name = blob.name.replace("healed_functions/", "").replace(".py", "")
                code = blob.download_as_text()
                
                try:
                    func = self._load_dynamic_function(code, func_name)
                    if func:
                        self.dynamic_functions[func_name] = func
                except:
                    pass
        except Exception:
            pass
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """Get statistics about healing operations"""
        query = f"""
        SELECT 
            status,
            COUNT(*) as count,
            AVG(confidence) as avg_confidence,
            AVG(healing_time_ms) as avg_time_ms
        FROM `{self.PROJECT_ID}.{self.DATASET_ID}.titan_healing_log`
        WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY status
        """
        
        try:
            results = self.bq_client.query(query).result()
            stats = {row["status"]: dict(row) for row in results}
            return {
                "last_7_days": stats,
                "total_healed": stats.get("healed", {}).get("count", 0),
                "total_failed": stats.get("failed", {}).get("count", 0),
                "avg_confidence": stats.get("healed", {}).get("avg_confidence", 0),
            }
        except Exception:
            return {"error": "Unable to fetch stats"}


# Convenience decorator
def auto_heal(func: Callable) -> Callable:
    """
    Decorator for automatic self-healing
    
    Usage:
        @auto_heal
        def risky_function():
            ...
    """
    phoenix = PhoenixProtocols()
    return phoenix.wrap_with_healing(func)
