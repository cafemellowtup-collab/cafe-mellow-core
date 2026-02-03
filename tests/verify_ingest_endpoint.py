"""
Deep Verification Script for Phase 2B: Ingestion Endpoint
==========================================================
Tests the /api/v1/ingest/file endpoint without running the full server.

Test Cases:
1. CSV Upload - Valid CSV file should return 200 OK
2. Excel Upload - Valid XLSX file should return 200 OK
3. Bad File Type - .txt file should return 400 Error
4. Missing Header - No X-Tenant-ID should return 422 Validation Error
"""

import io
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from fastapi.testclient import TestClient

# Import the FastAPI app
from api.main import app

client = TestClient(app)

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def test_csv_upload():
    """Test 1: Valid CSV file upload"""
    print("\n" + "=" * 60)
    print("TEST 1: CSV File Upload")
    print("=" * 60)
    
    # Create in-memory CSV
    csv_data = """Date,Amount,Description
2024-01-15,1500.50,Sale Item A
2024-01-16,2300.00,Sale Item B
2024-01-17,875.25,Sale Item C"""
    
    csv_bytes = io.BytesIO(csv_data.encode("utf-8"))
    
    try:
        response = client.post(
            "/api/v1/ingest/file",
            files={"file": ("test_sales.csv", csv_bytes, "text/csv")},
            headers={"X-Tenant-ID": "test-tenant-001"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "received" and data.get("rows") == 3:
                print(f"\n{PASS} CSV parsing works correctly!")
                print(f"   - Rows: {data['rows']}")
                print(f"   - Columns: {data['columns']}")
                return True
            else:
                print(f"\n{FAIL} Unexpected response data")
                return False
        else:
            print(f"\n{FAIL} Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n{FAIL} Exception: {str(e)}")
        return False


def test_excel_upload():
    """Test 2: Valid Excel file upload"""
    print("\n" + "=" * 60)
    print("TEST 2: Excel (XLSX) File Upload")
    print("=" * 60)
    
    # Create in-memory Excel file using pandas
    df = pd.DataFrame({
        "Order_ID": ["ORD001", "ORD002", "ORD003"],
        "Date": ["2024-01-15", "2024-01-16", "2024-01-17"],
        "Amount": [1500.50, 2300.00, 875.25],
        "Customer": ["John Doe", "Jane Smith", "Bob Wilson"]
    })
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    try:
        response = client.post(
            "/api/v1/ingest/file",
            files={"file": ("test_orders.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers={"X-Tenant-ID": "test-tenant-001"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "received" and data.get("rows") == 3:
                print(f"\n{PASS} Excel parsing works correctly!")
                print(f"   - Rows: {data['rows']}")
                print(f"   - Columns: {data['columns']}")
                return True
            else:
                print(f"\n{FAIL} Unexpected response data")
                return False
        else:
            print(f"\n{FAIL} Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n{FAIL} Exception: {str(e)}")
        return False


def test_bad_file_type():
    """Test 3: Unsupported file type (.txt) should return 400"""
    print("\n" + "=" * 60)
    print("TEST 3: Bad File Type (.txt)")
    print("=" * 60)
    
    txt_data = "This is just a text file, not tabular data."
    txt_bytes = io.BytesIO(txt_data.encode("utf-8"))
    
    try:
        response = client.post(
            "/api/v1/ingest/file",
            files={"file": ("bad_file.txt", txt_bytes, "text/plain")},
            headers={"X-Tenant-ID": "test-tenant-001"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            print(f"\n{PASS} Correctly rejected unsupported file type!")
            return True
        else:
            print(f"\n{FAIL} Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n{FAIL} Exception: {str(e)}")
        return False


def test_missing_tenant_header():
    """Test 4: Missing X-Tenant-ID header should return 422"""
    print("\n" + "=" * 60)
    print("TEST 4: Missing X-Tenant-ID Header")
    print("=" * 60)
    
    csv_data = "Date,Amount\n2024-01-15,100"
    csv_bytes = io.BytesIO(csv_data.encode("utf-8"))
    
    try:
        response = client.post(
            "/api/v1/ingest/file",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
            # NO X-Tenant-ID header
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 422:
            print(f"\n{PASS} Correctly requires X-Tenant-ID header!")
            return True
        else:
            print(f"\n{FAIL} Expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n{FAIL} Exception: {str(e)}")
        return False


def test_health_endpoint():
    """Bonus Test: Health endpoint should return 200"""
    print("\n" + "=" * 60)
    print("BONUS: Health Endpoint")
    print("=" * 60)
    
    try:
        response = client.get("/api/v1/ingest/health")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print(f"\n{PASS} Health endpoint works!")
            return True
        else:
            print(f"\n{FAIL} Expected 200, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n{FAIL} Exception: {str(e)}")
        return False


def main():
    print("\n" + "#" * 70)
    print("#  DEEP VERIFICATION: Phase 2B Ingestion Endpoint")
    print("#" * 70)
    
    results = {
        "CSV Upload": test_csv_upload(),
        "Excel Upload": test_excel_upload(),
        "Bad File Type": test_bad_file_type(),
        "Missing Header": test_missing_tenant_header(),
        "Health Check": test_health_endpoint(),
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("DEEP ANALYSIS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = PASS if result else FAIL
        print(f"  {status} {test_name}")
    
    print("-" * 70)
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Phase 2B is VERIFIED and PRODUCTION-READY.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review and fix before proceeding.")
    
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
