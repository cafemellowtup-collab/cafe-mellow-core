"""
TITAN ERP Comprehensive API Test Suite
======================================
Tests all endpoints to ensure system integrity before deployment.

Run with: python -m pytest tests/test_all_endpoints.py -v
Or: python tests/test_all_endpoints.py (standalone)
"""

import sys
import os

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import requests
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "https://cafe-mellow-backend-564285438043.asia-south1.run.app"
LOCAL_URL = "http://localhost:8000"
TENANT_ID = "cafe_mellow_001"

# Use production URL by default, can switch to local
API_URL = BASE_URL


class TestResult:
    def __init__(self, name: str, passed: bool, message: str, duration_ms: int = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration_ms = duration_ms


class TitanTestSuite:
    """Comprehensive test suite for all TITAN ERP endpoints"""
    
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None,
        params: Dict = None,
        timeout: int = 30
    ) -> Tuple[bool, Any, int]:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        start = datetime.now()
        
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=timeout)
            elif method == "POST":
                response = requests.post(url, json=data, params=params, timeout=timeout)
            elif method == "DELETE":
                response = requests.delete(url, params=params, timeout=timeout)
            else:
                return False, {"error": f"Unknown method: {method}"}, 0
            
            duration = int((datetime.now() - start).total_seconds() * 1000)
            
            try:
                data = response.json()
            except:
                data = {"raw": response.text[:500]}
            
            return response.status_code < 400, data, response.status_code, duration
            
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0, timeout * 1000
        except Exception as e:
            return False, {"error": str(e)}, 0, 0
    
    def add_result(self, name: str, passed: bool, message: str, duration_ms: int = 0):
        """Add test result"""
        self.results.append(TestResult(name, passed, message, duration_ms))
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    # ============ Core Health Checks ============
    
    def test_main_health(self):
        """Test main API health endpoint"""
        success, data, status, duration = self._make_request("GET", "/health")
        passed = success and data.get("ok") == True
        self.add_result(
            "Main Health Check",
            passed,
            f"Status: {status}, Version: {data.get('version', 'N/A')}",
            duration
        )
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        success, data, status, duration = self._make_request("GET", "/")
        passed = success
        self.add_result(
            "Root Endpoint",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Intelligence Engine ============
    
    def test_intelligence_health(self):
        """Test intelligence engine health"""
        success, data, status, duration = self._make_request(
            "GET", 
            f"/api/v1/intelligence/health?tenant_id={TENANT_ID}"
        )
        passed = success and data.get("status") in ["healthy", "degraded"]
        self.add_result(
            "Intelligence Health",
            passed,
            f"Status: {data.get('status', 'unknown')}",
            duration
        )
    
    def test_intelligence_metrics(self):
        """Test real-time metrics endpoint"""
        success, data, status, duration = self._make_request(
            "GET",
            f"/api/v1/intelligence/metrics?tenant_id={TENANT_ID}"
        )
        passed = success and data.get("ok") == True
        self.add_result(
            "Intelligence Metrics",
            passed,
            f"Revenue 7d: {data.get('revenue', {}).get('last_7d', 'N/A')}",
            duration
        )
    
    def test_intelligence_classify(self):
        """Test query classification"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/intelligence/classify",
            params={"query": "What is my revenue this week?"}
        )
        passed = success and data.get("intent") is not None
        self.add_result(
            "Query Classification",
            passed,
            f"Intent: {data.get('intent', 'unknown')}",
            duration
        )
    
    def test_intelligence_anomalies(self):
        """Test anomaly detection"""
        success, data, status, duration = self._make_request(
            "GET",
            f"/api/v1/intelligence/anomalies?tenant_id={TENANT_ID}"
        )
        passed = success and "anomalies" in data
        self.add_result(
            "Anomaly Detection",
            passed,
            f"Anomalies found: {data.get('count', 0)}",
            duration
        )
    
    # ============ Reports ============
    
    def test_reports_health(self):
        """Test reports health"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/reports/health"
        )
        passed = success and data.get("ok") == True
        self.add_result(
            "Reports Health",
            passed,
            f"Templates: {data.get('templates_count', 0)}",
            duration
        )
    
    def test_reports_templates(self):
        """Test report templates listing"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/reports/templates"
        )
        passed = success and "templates" in data
        self.add_result(
            "Report Templates",
            passed,
            f"Templates: {len(data.get('templates', []))}",
            duration
        )
    
    def test_reports_quick_today(self):
        """Test quick daily report"""
        success, data, status, duration = self._make_request(
            "GET",
            f"/api/v1/reports/quick/today?tenant_id={TENANT_ID}"
        )
        passed = success and data.get("report_type") == "daily_summary"
        self.add_result(
            "Quick Report (Today)",
            passed,
            f"Generated: {data.get('generated_at', 'N/A')[:19] if data.get('generated_at') else 'N/A'}",
            duration
        )
    
    # ============ Master Dashboard ============
    
    def test_master_health(self):
        """Test master dashboard health"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/master/health"
        )
        passed = success and data.get("ok") == True
        self.add_result(
            "Master Dashboard Health",
            passed,
            f"Status: {status}",
            duration
        )
    
    def test_master_stats(self):
        """Test master stats endpoint"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/master/stats"
        )
        passed = success
        self.add_result(
            "Master Stats",
            passed,
            f"Total tenants: {data.get('total_tenants', 'N/A')}",
            duration
        )
    
    # ============ Semantic Brain ============
    
    def test_brain_health(self):
        """Test semantic brain health"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/brain/health"
        )
        passed = success and data.get("ok") == True
        self.add_result(
            "Semantic Brain Health",
            passed,
            f"Capabilities: {len(data.get('capabilities', []))}",
            duration
        )
    
    def test_brain_categories(self):
        """Test brain categories listing"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/brain/categories"
        )
        passed = success and "categories" in data
        self.add_result(
            "Brain Categories",
            passed,
            f"Categories: {len(data.get('categories', []))}",
            duration
        )
    
    # ============ Chat ============
    
    def test_chat_non_streaming(self):
        """Test non-streaming chat endpoint"""
        success, data, status, duration = self._make_request(
            "POST",
            "/api/v1/chat",
            data={
                "message": "Hello",
                "org_id": TENANT_ID,
                "location_id": "main",
            },
            timeout=60
        )
        passed = success and (data.get("ok") == True or "answer" in data)
        self.add_result(
            "Chat (Non-streaming)",
            passed,
            f"Response length: {len(data.get('answer', ''))} chars" if passed else f"Error: {str(data)[:100]}",
            duration
        )
    
    # ============ Analytics ============
    
    def test_analytics_summary(self):
        """Test analytics summary"""
        success, data, status, duration = self._make_request(
            "GET",
            f"/api/v1/analytics/summary?org_id={TENANT_ID}"
        )
        passed = success
        self.add_result(
            "Analytics Summary",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Auth ============
    
    def test_auth_health(self):
        """Test auth system"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/auth/health"
        )
        passed = success
        self.add_result(
            "Auth Health",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Universal Adapter ============
    
    def test_adapter_health(self):
        """Test universal adapter health"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/adapter/health"
        )
        passed = success and data.get("ok") == True
        self.add_result(
            "Universal Adapter Health",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Oracle ============
    
    def test_oracle_health(self):
        """Test oracle endpoint"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/oracle/health"
        )
        passed = success
        self.add_result(
            "Oracle Health",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Forecast ============
    
    def test_forecast_health(self):
        """Test forecast endpoint"""
        success, data, status, duration = self._make_request(
            "GET",
            "/api/v1/forecast/health"
        )
        passed = success
        self.add_result(
            "Forecast Health",
            passed,
            f"Status: {status}",
            duration
        )
    
    # ============ Run All Tests ============
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("TITAN ERP API Test Suite")
        print(f"Target: {self.base_url}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")
        
        # Core health checks
        print("🔍 Running Core Health Checks...")
        self.test_main_health()
        self.test_root_endpoint()
        
        # Intelligence Engine
        print("\n🧠 Testing Intelligence Engine...")
        self.test_intelligence_health()
        self.test_intelligence_metrics()
        self.test_intelligence_classify()
        self.test_intelligence_anomalies()
        
        # Reports
        print("\n📊 Testing Reports...")
        self.test_reports_health()
        self.test_reports_templates()
        self.test_reports_quick_today()
        
        # Master Dashboard
        print("\n🏛️ Testing Master Dashboard...")
        self.test_master_health()
        self.test_master_stats()
        
        # Semantic Brain
        print("\n🧬 Testing Semantic Brain...")
        self.test_brain_health()
        self.test_brain_categories()
        
        # Chat
        print("\n💬 Testing Chat...")
        self.test_chat_non_streaming()
        
        # Analytics
        print("\n📈 Testing Analytics...")
        self.test_analytics_summary()
        
        # Auth
        print("\n🔐 Testing Auth...")
        self.test_auth_health()
        
        # Universal Adapter
        print("\n🔌 Testing Universal Adapter...")
        self.test_adapter_health()
        
        # Oracle & Forecast
        print("\n🔮 Testing Oracle & Forecast...")
        self.test_oracle_health()
        self.test_forecast_health()
        
        # Print results
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            print(f"{status} {result.name}")
            print(f"   {result.message}")
            if result.duration_ms > 0:
                print(f"   Duration: {result.duration_ms}ms")
        
        print("\n" + "-" * 60)
        print(f"Total: {self.total_tests} | Passed: {self.passed_tests} | Failed: {self.failed_tests}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️ {self.failed_tests} test(s) failed")
        
        print("=" * 60 + "\n")
        
        return self.failed_tests == 0


def main():
    """Main entry point"""
    # Check for local testing flag
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        url = LOCAL_URL
        print("Using local server...")
    else:
        url = API_URL
    
    suite = TitanTestSuite(url)
    success = suite.run_all()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
