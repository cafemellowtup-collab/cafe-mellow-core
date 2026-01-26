#!/usr/bin/env python3
"""
GENESIS PROTOCOL - Startup Validation Script
Validates all dependencies and configuration before starting the system
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pillars.config_vault import EffectiveSettings
from google.cloud import bigquery


class ValidationResult:
    def __init__(self):
        self.passed = []
        self.warnings = []
        self.errors = []
    
    def add_pass(self, check: str):
        self.passed.append(check)
        print(f"✅ {check}")
    
    def add_warning(self, check: str, message: str):
        self.warnings.append((check, message))
        print(f"⚠️  {check}: {message}")
    
    def add_error(self, check: str, message: str):
        self.errors.append((check, message))
        print(f"❌ {check}: {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")
        print("="*60)
        
        if self.errors:
            print("\n🚨 CRITICAL ERRORS - System cannot start:")
            for check, msg in self.errors:
                print(f"  • {check}: {msg}")
            return False
        
        if self.warnings:
            print("\n⚠️  WARNINGS - System may have limited functionality:")
            for check, msg in self.warnings:
                print(f"  • {check}: {msg}")
        
        if not self.errors:
            print("\n✅ ALL CRITICAL CHECKS PASSED - System ready to start!")
            return True
        
        return False


def validate_system():
    """Run all validation checks"""
    print("🧬 GENESIS PROTOCOL - Startup Validation")
    print("="*60 + "\n")
    
    result = ValidationResult()
    
    # 1. Check Python version
    print("📌 Checking Python Version...")
    if sys.version_info >= (3, 10):
        result.add_pass(f"Python Version: {sys.version_info.major}.{sys.version_info.minor}")
    else:
        result.add_error("Python Version", f"Requires Python 3.10+, found {sys.version_info.major}.{sys.version_info.minor}")
    
    # 2. Check required files
    print("\n📌 Checking Required Files...")
    required_files = [
        "settings.py",
        "pillars/config_vault.py",
        "api/main.py",
        "backend/core/ledger/models.py",
        "backend/core/security/models.py",
    ]
    
    for file_path in required_files:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            result.add_pass(f"File exists: {file_path}")
        else:
            result.add_error(f"File missing: {file_path}", "Critical file not found")
    
    # 3. Check service account key
    print("\n📌 Checking BigQuery Credentials...")
    try:
        cfg = EffectiveSettings()
        key_file = Path(cfg.KEY_FILE)
        
        if key_file.exists():
            result.add_pass(f"Service key found: {cfg.KEY_FILE}")
            
            # Try to initialize BigQuery client
            try:
                client = bigquery.Client.from_service_account_json(str(key_file))
                result.add_pass("BigQuery client initialized")
                
                # Test query
                try:
                    query = f"SELECT 1 as test"
                    list(client.query(query).result())
                    result.add_pass("BigQuery connection successful")
                except Exception as e:
                    result.add_warning("BigQuery Connection", f"Cannot connect: {str(e)[:100]}")
                
            except Exception as e:
                result.add_error("BigQuery Client", f"Cannot initialize: {str(e)[:100]}")
        else:
            result.add_error("Service Key", f"File not found: {cfg.KEY_FILE}")
    
    except Exception as e:
        result.add_error("Configuration", f"Cannot load config: {str(e)[:100]}")
    
    # 4. Check environment variables
    print("\n📌 Checking Environment Variables...")
    
    # Critical
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        result.add_pass("GEMINI_API_KEY is set")
    else:
        result.add_warning("GEMINI_API_KEY", "Not set - AI features may not work")
    
    # Optional but recommended
    cron_secret = os.getenv("CRON_SECRET")
    if cron_secret:
        result.add_pass("CRON_SECRET is set")
    else:
        result.add_warning("CRON_SECRET", "Not set - cron endpoints will reject all requests")
    
    # R2 Storage (optional)
    r2_keys = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"]
    r2_configured = all(os.getenv(key) for key in r2_keys)
    if r2_configured:
        result.add_pass("R2 Storage configured")
    else:
        result.add_warning("R2 Storage", "Not configured - file uploads will fail")
    
    # 5. Check required Python packages
    print("\n📌 Checking Python Dependencies...")
    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("google.cloud.bigquery", "BigQuery Client"),
        ("boto3", "Boto3 (for R2)"),
    ]
    
    for module_name, display_name in required_packages:
        try:
            __import__(module_name)
            result.add_pass(f"Package installed: {display_name}")
        except ImportError:
            result.add_error(f"Package missing: {display_name}", f"Run: pip install {module_name}")
    
    # 6. Check BigQuery tables
    print("\n📌 Checking BigQuery Tables...")
    try:
        cfg = EffectiveSettings()
        if os.path.exists(cfg.KEY_FILE):
            client = bigquery.Client.from_service_account_json(cfg.KEY_FILE)
            
            required_tables = [
                "ledger_universal",
                "users",
                "roles",
                "entities",
            ]
            
            for table_name in required_tables:
                table_id = f"{cfg.PROJECT_ID}.{cfg.DATASET_ID}.{table_name}"
                try:
                    client.get_table(table_id)
                    result.add_pass(f"Table exists: {table_name}")
                except Exception:
                    result.add_warning(f"Table missing: {table_name}", "Run: python scripts/setup_genesis.py")
    except Exception as e:
        result.add_warning("Table Check", f"Cannot check tables: {str(e)[:100]}")
    
    # 7. Check ports
    print("\n📌 Checking Port Availability...")
    import socket
    
    def is_port_available(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False
    
    if is_port_available(8000):
        result.add_pass("Port 8000 available for API")
    else:
        result.add_warning("Port 8000", "Port in use - API may already be running")
    
    if is_port_available(8501):
        result.add_pass("Port 8501 available for Streamlit")
    else:
        result.add_warning("Port 8501", "Port in use - Streamlit may already be running")
    
    # Summary
    return result.summary()


if __name__ == "__main__":
    success = validate_system()
    sys.exit(0 if success else 1)
