"""Quick diagnostic to see actual error messages"""
import requests
import json

API_BASE = "http://127.0.0.1:8000"

print("🔍 Diagnosing API Errors...\n")

# Test 1: Forecast
print("1️⃣ Testing Forecast Endpoint:")
try:
    res = requests.post(
        f"{API_BASE}/api/v1/forecast/daily",
        json={
            "org_id": "test_org",
            "location_id": "test_location",
            "forecast_date": "2026-01-27",
            "include_weather": True
        },
        timeout=10
    )
    print(f"   Status: {res.status_code}")
    if res.status_code != 200:
        print(f"   Error: {res.text[:500]}")
except Exception as e:
    print(f"   Exception: {e}")

print()

# Test 2: Metacognitive
print("2️⃣ Testing Metacognitive Endpoint:")
try:
    res = requests.get(
        f"{API_BASE}/api/v1/chat/metacognitive/strategies",
        params={
            "org_id": "test_org",
            "location_id": "test_location",
            "status": "active"
        },
        timeout=10
    )
    print(f"   Status: {res.status_code}")
    if res.status_code != 200:
        print(f"   Error: {res.text[:500]}")
except Exception as e:
    print(f"   Exception: {e}")

print()

# Test 3: Chat (quick test)
print("3. Testing Chat Endpoint:")
try:
    res = requests.post(
        f"{API_BASE}/api/v1/chat",
        json={
            "message": "Hello",
            "org_id": "test_org",
            "location_id": "test_location"
        },
        timeout=5
    )
    print(f"   Status: {res.status_code}")
    if res.status_code != 200:
        print(f"   Error: {res.text[:500]}")
except Exception as e:
    print(f"   Exception: {e}")
