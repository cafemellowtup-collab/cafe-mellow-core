"""
Fortress Chaos Test Suite
========================
Validates the robustness of the Fortress upgrade by testing various edge cases:
1. Perfect File: Valid CSV with new ghost item
2. Duplicate Upload: Same file, expect duplicates
3. Junk File: Random .txt, expect rejection
4. Empty File: Headers only, expect graceful handling
"""

import io
import os
import time
import requests
import pandas as pd
from datetime import datetime

# Test configuration
API_URL = "http://localhost:8000/api/v1/ingest"
TENANT_ID = "test_tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}

def create_test_sales_csv(items=None):
    """Create a test sales CSV file"""
    if items is None:
        items = ["NewGhostBurger"]
    
    data = {
        "Date": [datetime.now().strftime("%Y-%m-%d")],
        "Amount": [15.99],
        "Item": items,
        "Quantity": [1]
    }
    df = pd.DataFrame(data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def wait_for_processing(file_id, timeout=30):
    """Wait for file processing to complete"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_URL}/status", headers=HEADERS)
            if response.status_code == 200:
                for file_status in response.json():
                    if file_status["file_id"] == file_id:
                        if file_status["status"] in ["completed", "failed", "rejected"]:
                            print(f"Status: {file_status['status']}")
                            if file_status.get('error'):
                                print(f"Error: {file_status['error']}")
                            return file_status
            time.sleep(1)
        except requests.exceptions.ConnectionError:
            print("Waiting for server...")
            time.sleep(2)
    raise TimeoutError("File processing timed out")

def test_scenario_1_perfect_file():
    """Test uploading a valid CSV with a new ghost item"""
    print("\n🧪 Scenario 1: Perfect File with Ghost Item")
    
    # Create test file
    csv_content = create_test_sales_csv()
    files = {"file": ("test_sales.csv", csv_content, "text/csv")}
    
    try:
        # Upload file
        response = requests.post(f"{API_URL}/file", headers=HEADERS, files=files)
        assert response.status_code == 200, f"Upload failed: {response.text}"
        
        # Wait for processing
        file_status = wait_for_processing(response.json()["file_id"])
        
        # Verify results
        success = (
            file_status["status"] == "completed" and
            file_status.get("ghost_items", 0) >= 1 and
            file_status.get("error") is None
        )
        
        print(f"✅ Pass: {success}")
        print(f"Ghost Items: {file_status.get('ghost_items', 0)}")
        print(f"Events Added: {file_status.get('new_events', 0)}")
        return success
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_scenario_2_duplicate():
    """Test uploading the same file twice"""
    print("\n🧪 Scenario 2: Duplicate Upload")
    
    try:
        # Create and upload first file
        csv_content = create_test_sales_csv(["ExistingBurger"])
        files = {"file": ("sales_dup.csv", csv_content, "text/csv")}
        
        response = requests.post(f"{API_URL}/file", headers=HEADERS, files=files)
        assert response.status_code == 200, f"First upload failed: {response.text}"
        wait_for_processing(response.json()["file_id"])
        
        # Upload same file again
        response = requests.post(f"{API_URL}/file", headers=HEADERS, files=files)
        assert response.status_code == 200, f"Second upload failed: {response.text}"
        
        # Wait for processing
        file_status = wait_for_processing(response.json()["file_id"])
        
        # Verify results
        success = (
            file_status["status"] == "completed" and
            file_status.get("duplicates", 0) > 0 and
            file_status.get("new_events", 0) == 0
        )
        
        print(f"✅ Pass: {success}")
        print(f"Duplicates: {file_status.get('duplicates', 0)}")
        print(f"New Events: {file_status.get('new_events', 0)}")
        return success
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_scenario_3_junk_file():
    """Test uploading a junk .txt file"""
    print("\n🧪 Scenario 3: Junk File")
    
    try:
        # Create junk file
        junk_content = "This is not a CSV file\nJust some random text\n"
        files = {"file": ("junk.txt", junk_content, "text/plain")}
        
        # Upload file
        response = requests.post(f"{API_URL}/file", headers=HEADERS, files=files)
        
        # Verify rejection
        success = response.status_code == 400
        print(f"✅ Pass: {success}")
        print(f"Status Code: {response.status_code}")
        if not success:
            print(f"Response: {response.text}")
        return success
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_scenario_4_empty_file():
    """Test uploading a CSV with headers but no data"""
    print("\n🧪 Scenario 4: Empty File")
    
    try:
        # Create empty CSV with headers
        headers = "Date,Amount,Item,Quantity\n"
        files = {"file": ("empty.csv", headers, "text/csv")}
        
        # Upload file
        response = requests.post(f"{API_URL}/file", headers=HEADERS, files=files)
        
        if response.status_code == 200:
            # If accepted, should handle gracefully
            file_status = wait_for_processing(response.json()["file_id"])
            success = file_status["status"] in ["completed", "failed", "rejected"]
            print(f"✅ Pass: {success} (Handled gracefully)")
            print(f"Status: {file_status['status']}")
            if file_status.get("error"):
                print(f"Error: {file_status['error']}")
        else:
            # If rejected immediately, that's fine too
            success = response.status_code == 400
            print(f"✅ Pass: {success} (Rejected cleanly)")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        
        return success
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all test scenarios and print report card"""
    print("\n🏰 FORTRESS CHAOS TEST SUITE")
    print("=" * 50)
    
    results = {
        "Perfect File": test_scenario_1_perfect_file(),
        "Duplicate Upload": test_scenario_2_duplicate(),
        "Junk File": test_scenario_3_junk_file(),
        "Empty File": test_scenario_4_empty_file()
    }
    
    print("\n📊 REPORT CARD")
    print("=" * 50)
    for scenario, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {scenario}")
    
    total_passed = sum(1 for passed in results.values() if passed)
    print(f"\nTotal Score: {total_passed}/{len(results)}")
    
    return all(results.values())

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
