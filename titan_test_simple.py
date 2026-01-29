import requests
import json
import time

print("TITAN 360 Testing - Core Systems Check")
print("=" * 50)

# Test API Health
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print("API Health: PASS - " + str(data.get("status")) + " v" + str(data.get("version")))
    else:
        print("API Health: FAIL - Status " + str(response.status_code))
except Exception as e:
    print("API Health: FAIL - " + str(e))

# Test TITAN AI Intelligence
try:
    chat_data = {"message": "Show me our current business performance with exact figures", "session_id": "test_001"}
    response = requests.post("http://localhost:8000/chat", json=chat_data, timeout=30)
    if response.status_code == 200:
        result = response.json()
        answer = result.get("answer", "")
        print("TITAN AI: PASS - Responding (" + str(len(answer)) + " chars)")
        
        # Check intelligence indicators
        intelligence = 0
        if "data" in answer.lower(): intelligence += 1
        if len(answer) > 100: intelligence += 1
        if any(word in answer.lower() for word in ["recommend", "analysis", "insight"]): intelligence += 1
        print("Intelligence Score: " + str(intelligence) + "/3")
    else:
        print("TITAN AI: FAIL - Status " + str(response.status_code))
except Exception as e:
    print("TITAN AI: FAIL - " + str(e))

# Test Reports
endpoints = ["/reports/daily-summary", "/reports/financial-overview", "/alerts/current", "/metrics/data-quality"]
print("\nTesting Reports & Endpoints...")
for endpoint in endpoints:
    try:
        response = requests.get("http://localhost:8000" + endpoint, timeout=10)
        status = "PASS" if response.status_code == 200 else "FAIL"
        print(endpoint + ": " + status + " (HTTP " + str(response.status_code) + ")")
    except Exception as e:
        print(endpoint + ": FAIL - " + str(e))

# Test Authentication
print("\nTesting Authentication...")
try:
    signup_data = {
        "username": "test_user_" + str(int(time.time())),
        "email": "test_" + str(int(time.time())) + "@example.com", 
        "password": "TestPass123!",
        "full_name": "Test User"
    }
    
    response = requests.post("http://localhost:8000/auth/signup", json=signup_data, timeout=10)
    if response.status_code in [200, 201, 409]:
        print("Auth Signup: PASS (Status " + str(response.status_code) + ")")
    else:
        print("Auth Signup: FAIL (Status " + str(response.status_code) + ")")
        
except Exception as e:
    print("Auth Signup: FAIL - " + str(e))

print("\nCore testing complete!")
