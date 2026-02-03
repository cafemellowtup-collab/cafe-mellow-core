"""
Upload Stability Test
=====================
Verifies that the backend survives file uploads without crashing.
"""

import os
import sys
import time
import requests

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

API_BASE = "http://localhost:8000/api/v1"
TENANT_ID = "demo-cafe"

def create_test_csv():
    """Create a simple test CSV file"""
    csv_content = """date,item,amount,category
2026-01-01,Coffee Beans,1500,expense
2026-01-02,Milk,500,expense
2026-01-03,Sugar,200,expense
2026-01-04,Revenue,5000,income
2026-01-05,Salaries,3000,expense
"""
    test_file = "test_upload.csv"
    with open(test_file, "w") as f:
        f.write(csv_content)
    return test_file

def test_upload_stability():
    """
    Test sequence:
    1. Create test CSV
    2. POST /api/v1/ingest/file
    3. Wait 2 seconds
    4. GET /api/v1/ingest/status
    5. Report pass/fail
    """
    print("=" * 50)
    print("UPLOAD STABILITY TEST")
    print("=" * 50)
    
    # Step 1: Create test file
    print("\n[1] Creating test CSV...")
    test_file = create_test_csv()
    print(f"    Created: {test_file}")
    
    # Step 2: Upload file
    print("\n[2] Uploading file to /api/v1/ingest/file...")
    try:
        with open(test_file, "rb") as f:
            response = requests.post(
                f"{API_BASE}/ingest/file",
                files={"file": ("test_upload.csv", f, "text/csv")},
                headers={"X-Tenant-ID": TENANT_ID},
                timeout=30
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Upload successful: {data}")
            file_id = data.get("file_id")
        else:
            print(f"[FAIL] Upload failed: {response.status_code} - {response.text}")
            file_id = None
            
    except requests.exceptions.ConnectionError as e:
        print(f"[FAIL] CONNECTION ERROR during upload: {e}")
        print("\nFAIL: Server may have crashed during upload!")
        cleanup(test_file)
        return False
    except Exception as e:
        print(f"[FAIL] Upload error: {type(e).__name__}: {e}")
        cleanup(test_file)
        return False
    
    # Step 3: Wait for processing
    print("\n[3] Waiting 2 seconds for background processing...")
    time.sleep(2)
    
    # Step 4: Check status endpoint
    print("\n[4] Checking /api/v1/ingest/status...")
    try:
        response = requests.get(
            f"{API_BASE}/ingest/status",
            headers={"X-Tenant-ID": TENANT_ID},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Status endpoint alive! Files: {len(data)}")
            
            # Find our file
            if file_id:
                for f in data:
                    if f.get("file_id") == file_id:
                        status = f.get("status")
                        error = f.get("error")
                        print(f"    File status: {status}")
                        if error:
                            print(f"    Error: {error}")
                        break
        else:
            print(f"[WARN] Status returned: {response.status_code}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"[FAIL] CONNECTION ERROR on status check: {e}")
        print("\n" + "=" * 50)
        print("FAIL: Server Crashed!")
        print("=" * 50)
        print("\nThe server died after the upload. Check backend terminal for traceback.")
        cleanup(test_file)
        return False
    except Exception as e:
        print(f"[FAIL] Status check error: {type(e).__name__}: {e}")
        cleanup(test_file)
        return False
    
    # Success!
    print("\n" + "=" * 50)
    print("PASS: Server is Alive!")
    print("=" * 50)
    print("\nThe backend survived the upload test.")
    
    cleanup(test_file)
    return True

def cleanup(test_file):
    """Remove test file"""
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n[Cleanup] Removed {test_file}")
    except Exception:
        pass

if __name__ == "__main__":
    success = test_upload_stability()
    sys.exit(0 if success else 1)
