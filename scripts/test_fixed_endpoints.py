# -*- coding: utf-8 -*-
"""Test the fixed endpoints"""
import requests

API_BASE = "http://127.0.0.1:8000"

print("Testing fixed endpoints...\n")

# Test 1: Forecast (should work now)
print("1. Forecast:", end=" ")
try:
    res = requests.post(
        f"{API_BASE}/api/v1/forecast/daily",
        json={"org_id": "test", "location_id": "test", "forecast_date": "2026-01-27"},
        timeout=10
    )
    print(f"Status {res.status_code} - {'OK' if res.status_code in [200, 400] else 'FAIL'}")
except Exception as e:
    print(f"FAIL: {e}")

# Test 2: Metacognitive (should work now - table created)
print("2. Metacognitive:", end=" ")
try:
    res = requests.get(
        f"{API_BASE}/api/v1/chat/metacognitive/strategies",
        params={"org_id": "test", "location_id": "test", "status": "active"},
        timeout=10
    )
    print(f"Status {res.status_code} - {'OK' if res.status_code == 200 else 'FAIL'}")
except Exception as e:
    print(f"FAIL: {e}")

print("\nTo fix Chat timeout: Set GEMINI_API_KEY")
print("Option 1: Via UI at http://localhost:3000/settings")
print("Option 2: Via PowerShell: $env:GEMINI_API_KEY='your-key' then restart uvicorn")
