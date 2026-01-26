"""
Production Readiness Test Script
Tests all critical endpoints and features before deployment
"""
import requests
import sys
import json
from datetime import datetime, timedelta

API_BASE = "http://127.0.0.1:8000"
API_V1 = f"{API_BASE}/api/v1"

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "reset": "\033[0m"
}

def log_test(name: str, passed: bool, message: str = ""):
    status = f"{COLORS['green']}✓ PASS{COLORS['reset']}" if passed else f"{COLORS['red']}✗ FAIL{COLORS['reset']}"
    print(f"{status} | {name}")
    if message:
        print(f"     {message}")

def test_health():
    """Test API health endpoint"""
    try:
        res = requests.get(f"{API_BASE}/health", timeout=5)
        data = res.json()
        
        passed = (
            res.status_code == 200 and
            data.get("ok") is True and
            data.get("bq_connected") is True
        )
        
        log_test("Health Check", passed, f"BigQuery: {'Connected' if data.get('bq_connected') else 'Disconnected'}")
        return passed
    except Exception as e:
        log_test("Health Check", False, str(e))
        return False

def test_chat():
    """Test chat endpoints"""
    try:
        # Test non-streaming
        payload = {
            "message": "Test message",
            "org_id": "test_org",
            "location_id": "test_location"
        }
        res = requests.post(f"{API_V1}/chat", json=payload, timeout=10)
        
        passed = res.status_code == 200 or res.status_code == 400
        log_test("Chat Endpoint", passed, f"Status: {res.status_code}")
        return passed
    except Exception as e:
        log_test("Chat Endpoint", False, str(e))
        return False

def test_sync_status():
    """Test sync status endpoint"""
    try:
        res = requests.get(f"{API_V1}/sync/status", timeout=5)
        data = res.json()
        
        passed = res.status_code == 200 and data.get("ok") is True
        log_test("Sync Status", passed)
        return passed
    except Exception as e:
        log_test("Sync Status", False, str(e))
        return False

def test_forecast():
    """Test forecast endpoint"""
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "org_id": "test_org",
            "location_id": "test_location",
            "forecast_date": tomorrow,
            "include_weather": True
        }
        res = requests.post(f"{API_V1}/forecast/daily", json=payload, timeout=10)
        
        passed = res.status_code == 200 or res.status_code == 400
        log_test("Forecast Engine", passed, f"Status: {res.status_code}")
        return passed
    except Exception as e:
        log_test("Forecast Engine", False, str(e))
        return False

def test_metacognitive():
    """Test metacognitive endpoints"""
    try:
        # Test get strategies
        params = {
            "org_id": "test_org",
            "location_id": "test_location",
            "status": "active"
        }
        res = requests.get(f"{API_V1}/chat/metacognitive/strategies", params=params, timeout=5)
        
        passed = res.status_code == 200 or res.status_code == 400
        log_test("Metacognitive API", passed, f"Status: {res.status_code}")
        return passed
    except Exception as e:
        log_test("Metacognitive API", False, str(e))
        return False

def test_oracle():
    """Test oracle deduction endpoint"""
    try:
        payload = {
            "problem": "Maida inventory is -526g",
            "org_id": "test_org",
            "location_id": "test_location"
        }
        res = requests.post(f"{API_V1}/oracle/deduce", json=payload, timeout=10)
        
        passed = res.status_code == 200 or res.status_code == 400
        log_test("Oracle Deduction", passed, f"Status: {res.status_code}")
        return passed
    except Exception as e:
        log_test("Oracle Deduction", False, str(e))
        return False

def main():
    print(f"\n{COLORS['blue']}{'='*60}")
    print("🧪 TITAN ERP - Production Readiness Test")
    print(f"{'='*60}{COLORS['reset']}\n")
    
    print(f"{COLORS['yellow']}Testing API Endpoints...{COLORS['reset']}\n")
    
    tests = [
        test_health,
        test_chat,
        test_sync_status,
        test_forecast,
        test_metacognitive,
        test_oracle,
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
        print()
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"{COLORS['blue']}{'='*60}")
    print(f"Test Results: {passed}/{total} passed ({percentage:.0f}%)")
    print(f"{'='*60}{COLORS['reset']}\n")
    
    if percentage == 100:
        print(f"{COLORS['green']}✅ ALL TESTS PASSED - READY FOR PRODUCTION{COLORS['reset']}")
        return 0
    elif percentage >= 80:
        print(f"{COLORS['yellow']}⚠️  MOST TESTS PASSED - VERIFY FAILURES{COLORS['reset']}")
        return 1
    else:
        print(f"{COLORS['red']}❌ CRITICAL FAILURES - NOT READY FOR PRODUCTION{COLORS['reset']}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
