"""
TITAN 360° Comprehensive Testing Suite
Tests every aspect of the system for production readiness
"""

import requests
import json
import time
from datetime import datetime
import sys

class TitanTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
        
    def log_result(self, test_name, success, details="", error=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "error": str(error) if error else None
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"    └─ {details}")
        if error:
            print(f"    └─ ERROR: {error}")
        print()

    def test_api_health(self):
        """Test basic API health and connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "API Health Check", 
                    True, 
                    f"Status: {data.get('status')}, Version: {data.get('version')}"
                )
                return True
            else:
                self.log_result("API Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Health Check", False, error=e)
            return False

    def test_titan_ai_intelligence(self):
        """Test TITAN AI advanced intelligence and character"""
        test_queries = [
            {
                "message": "Analyze our business performance and provide proactive insights",
                "expected_features": ["tables", "analysis", "recommendations", "context"]
            },
            {
                "message": "What recipe optimizations can improve our margins?",
                "expected_features": ["data-driven", "specific", "actionable"]
            },
            {
                "message": "Show me billing shortcode suggestions for faster cashier operations",
                "expected_features": ["shortcodes", "efficiency", "user_experience"]
            }
        ]
        
        for i, query in enumerate(test_queries):
            try:
                payload = {
                    "message": query["message"],
                    "session_id": f"test_intelligence_{i}"
                }
                
                response = self.session.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    
                    # Test AI character and intelligence
                    intelligence_score = 0
                    if len(answer) > 100:  # Substantial response
                        intelligence_score += 1
                    if "₹" in answer or "data" in answer.lower():  # Uses real data
                        intelligence_score += 1
                    if any(word in answer.lower() for word in ["recommend", "suggest", "optimize"]):  # Proactive
                        intelligence_score += 1
                    if "table" in answer.lower() or "analysis" in answer.lower():  # Structured
                        intelligence_score += 1
                    
                    success = intelligence_score >= 2
                    self.log_result(
                        f"TITAN AI Intelligence Test {i+1}",
                        success,
                        f"Intelligence Score: {intelligence_score}/4, Response Length: {len(answer)} chars"
                    )
                else:
                    self.log_result(f"TITAN AI Intelligence Test {i+1}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"TITAN AI Intelligence Test {i+1}", False, error=e)

    def test_reports_generation(self):
        """Test comprehensive report generation"""
        report_endpoints = [
            "/reports/daily-summary",
            "/reports/financial-overview", 
            "/reports/inventory-status",
            "/reports/operational-brief"
        ]
        
        for endpoint in report_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    has_data = bool(data and len(str(data)) > 50)
                    self.log_result(
                        f"Report Generation: {endpoint}",
                        has_data,
                        f"Response size: {len(str(data))} chars"
                    )
                else:
                    self.log_result(f"Report Generation: {endpoint}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Report Generation: {endpoint}", False, error=e)

    def test_proactive_monitoring(self):
        """Test proactive background monitoring systems"""
        try:
            # Test alert system
            response = self.session.get(f"{self.base_url}/alerts/current", timeout=15)
            
            if response.status_code == 200:
                alerts = response.json()
                self.log_result(
                    "Proactive Alert System",
                    True,
                    f"Active alerts: {len(alerts.get('alerts', []))}"
                )
            else:
                self.log_result("Proactive Alert System", False, f"HTTP {response.status_code}")
                
            # Test data quality monitoring
            response = self.session.get(f"{self.base_url}/metrics/data-quality", timeout=15)
            
            if response.status_code == 200:
                metrics = response.json()
                quality_score = metrics.get('overall_quality', 0)
                self.log_result(
                    "Data Quality Monitoring",
                    quality_score > 0,
                    f"Quality Score: {quality_score}%"
                )
            else:
                self.log_result("Data Quality Monitoring", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Proactive Monitoring", False, error=e)

    def test_authentication_system(self):
        """Test authentication and security"""
        try:
            # Test signup endpoint
            signup_data = {
                "username": f"test_user_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPass123!",
                "full_name": "Test User"
            }
            
            response = self.session.post(f"{self.base_url}/auth/signup", json=signup_data, timeout=15)
            
            if response.status_code in [200, 201, 409]:  # 409 = user exists, which is fine
                self.log_result("Authentication - Signup", True, f"Status: {response.status_code}")
            else:
                self.log_result("Authentication - Signup", False, f"HTTP {response.status_code}")
                
            # Test login endpoint
            login_data = {
                "username": signup_data["username"],
                "password": signup_data["password"]
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data, timeout=15)
            
            if response.status_code == 200:
                token_data = response.json()
                has_token = "access_token" in token_data
                self.log_result("Authentication - Login", has_token, f"Token received: {has_token}")
            else:
                self.log_result("Authentication - Login", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Authentication System", False, error=e)

    def test_unique_erp_features(self):
        """Test unique ERP features that no other system offers"""
        unique_features = [
            ("/tenant/registry", "Multi-tenant Registry"),
            ("/compliance/audit-trail", "Compliance & Audit Trail"),
            ("/analytics/predictive", "Predictive Analytics"),
            ("/automation/workflows", "Automation Workflows"),
            ("/insights/proactive", "Proactive Business Insights")
        ]
        
        for endpoint, feature_name in unique_features:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"Unique ERP Feature: {feature_name}", True, "Available and responding")
                elif response.status_code == 404:
                    self.log_result(f"Unique ERP Feature: {feature_name}", False, "Endpoint not implemented")
                else:
                    self.log_result(f"Unique ERP Feature: {feature_name}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Unique ERP Feature: {feature_name}", False, error=e)

    def test_streaming_capabilities(self):
        """Test real-time streaming capabilities"""
        try:
            stream_data = {
                "message": "Stream me live business insights",
                "stream": True
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/stream",
                json=stream_data,
                timeout=20,
                stream=True
            )
            
            if response.status_code == 200:
                chunks_received = 0
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        chunks_received += 1
                        if chunks_received >= 3:  # Got streaming data
                            break
                
                self.log_result("Streaming Capabilities", chunks_received > 0, f"Chunks received: {chunks_received}")
            else:
                self.log_result("Streaming Capabilities", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Streaming Capabilities", False, error=e)

    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        print("🚀 TITAN 360° COMPREHENSIVE TESTING STARTED")
        print("=" * 60)
        
        # Core Infrastructure
        if not self.test_api_health():
            print("❌ API is not running! Please start the FastAPI server first.")
            return
        
        # Advanced AI Testing
        self.test_titan_ai_intelligence()
        
        # Reports and Analytics
        self.test_reports_generation()
        
        # Proactive Systems
        self.test_proactive_monitoring()
        
        # Security
        self.test_authentication_system()
        
        # Unique Features
        self.test_unique_erp_features()
        
        # Streaming
        self.test_streaming_capabilities()
        
        # Summary
        self.print_summary()

    def print_summary(self):
        """Print comprehensive test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print("=" * 60)
        print("🎯 TITAN COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🎯 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("=" * 60)
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result.get('error', 'See details above')}")
        
        print(f"\n🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = TitanTester()
    tester.run_comprehensive_test()
