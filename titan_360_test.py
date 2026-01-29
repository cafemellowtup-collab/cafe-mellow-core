"""
TITAN 360 Degree Comprehensive Testing Suite
Tests every aspect of the proactive AI business intelligence system
"""

import requests
import json
import time
from datetime import datetime
import threading
import sys

class Titan360Tester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, details="", error=None):
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
        print()

    def test_titan_ai_intelligence(self):
        """Test TITAN AI advanced intelligence capabilities"""
        print("=" * 60)
        print("TESTING TITAN AI INTELLIGENCE & CHARACTER")
        print("=" * 60)
        
        # Test queries that validate proactive business intelligence
        intelligence_tests = [
            {
                "query": "Analyze our business performance with exact figures and provide actionable insights",
                "expected_features": ["data", "analysis", "recommendations", "figures"]
            },
            {
                "query": "What recipe optimizations can improve our profit margins?",
                "expected_features": ["optimization", "profit", "recipe", "suggestions"]
            },
            {
                "query": "Show me billing shortcode suggestions for faster cashier operations",
                "expected_features": ["shortcode", "billing", "efficiency", "cashier"]
            },
            {
                "query": "Give me proactive business insights about potential issues",
                "expected_features": ["proactive", "insights", "business", "issues"]
            },
            {
                "query": "What milestones have we achieved and what should we focus on next?",
                "expected_features": ["milestones", "achievements", "focus", "next"]
            }
        ]
        
        total_intelligence_score = 0
        
        for i, test in enumerate(intelligence_tests, 1):
            try:
                print(f"AI Test {i}: {test['query'][:60]}...")
                
                response = self.session.post(
                    f"{self.base_url}/chat",
                    json={"message": test["query"], "session_id": f"intelligence_test_{i}"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("answer", "")
                    
                    # Calculate intelligence score
                    intelligence_score = 0
                    
                    # Check response quality
                    if len(answer) > 150: intelligence_score += 1  # Substantial response
                    if any(word in answer.lower() for word in ["data", "analysis", "table", "figure"]): intelligence_score += 1
                    if any(word in answer.lower() for word in ["recommend", "suggest", "optimize", "insight"]): intelligence_score += 1
                    if any(word in answer.lower() for word in ["tiruppur", "cafe", "business", "operations"]): intelligence_score += 1
                    if "TITAN" in answer: intelligence_score += 1
                    if any(feature in answer.lower() for feature in test["expected_features"]): intelligence_score += 1
                    
                    total_intelligence_score += intelligence_score
                    
                    self.log_test(
                        f"AI Intelligence Test {i}",
                        intelligence_score >= 3,
                        f"Score: {intelligence_score}/6, Response: {len(answer)} chars"
                    )
                else:
                    self.log_test(f"AI Intelligence Test {i}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"AI Intelligence Test {i}", False, error=e)
        
        # Overall intelligence assessment
        avg_intelligence = total_intelligence_score / len(intelligence_tests) if intelligence_tests else 0
        self.log_test(
            "TITAN Overall Intelligence Score",
            avg_intelligence >= 3.0,
            f"Average: {avg_intelligence:.1f}/6.0"
        )

    def test_reports_generation(self):
        """Test comprehensive report generation system"""
        print("=" * 60)
        print("TESTING REPORTS GENERATION SYSTEM")
        print("=" * 60)
        
        report_endpoints = [
            "/reports/daily-summary",
            "/reports/financial-overview",
            "/reports/inventory-status", 
            "/reports/operational-brief",
            "/reports/sales-analysis",
            "/reports/expense-breakdown"
        ]
        
        for endpoint in report_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    has_substantial_data = len(str(data)) > 100
                    self.log_test(
                        f"Report: {endpoint}",
                        has_substantial_data,
                        f"Data size: {len(str(data))} chars"
                    )
                else:
                    self.log_test(f"Report: {endpoint}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Report: {endpoint}", False, error=e)

    def test_proactive_monitoring(self):
        """Test proactive background monitoring and alert systems"""
        print("=" * 60)
        print("TESTING PROACTIVE MONITORING SYSTEMS")
        print("=" * 60)
        
        monitoring_endpoints = [
            ("/alerts/current", "Current Alerts"),
            ("/metrics/data-quality", "Data Quality Monitoring"),
            ("/analytics/business-health", "Business Health Analytics"),
            ("/monitoring/anomalies", "Anomaly Detection"),
            ("/insights/proactive", "Proactive Insights")
        ]
        
        for endpoint, name in monitoring_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(name, True, "System responding correctly")
                elif response.status_code == 404:
                    self.log_test(name, False, "Endpoint not implemented")
                else:
                    self.log_test(name, False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(name, False, error=e)

    def test_authentication_system(self):
        """Test authentication and security system"""
        print("=" * 60)
        print("TESTING AUTHENTICATION SYSTEM")
        print("=" * 60)
        
        # Test user registration
        test_user = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@cafemellow.com",
            "password": "TitanTest123!",
            "full_name": "Test User for TITAN"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/signup", json=test_user, timeout=15)
            signup_success = response.status_code in [200, 201, 409]  # 409 = user exists
            self.log_test("User Registration", signup_success, f"Status: {response.status_code}")
            
            if signup_success:
                # Test login
                login_data = {
                    "username": test_user["username"],
                    "password": test_user["password"]
                }
                
                response = self.session.post(f"{self.base_url}/auth/login", json=login_data, timeout=15)
                if response.status_code == 200:
                    token_data = response.json()
                    has_token = "access_token" in token_data
                    self.log_test("User Login", has_token, "JWT token received")
                    
                    if has_token:
                        # Test protected endpoint access
                        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                        response = self.session.get(f"{self.base_url}/auth/verify", headers=headers, timeout=10)
                        self.log_test("Token Verification", response.status_code == 200, "Token validation")
                else:
                    self.log_test("User Login", False, f"HTTP {response.status_code}")
                    
        except Exception as e:
            self.log_test("Authentication System", False, error=e)

    def test_unique_erp_features(self):
        """Test unique ERP features that distinguish TITAN from competitors"""
        print("=" * 60)
        print("TESTING UNIQUE ERP FEATURES")
        print("=" * 60)
        
        unique_features = [
            ("/phoenix/healing-status", "Phoenix Protocols Self-Healing"),
            ("/evolution/learning-metrics", "Evolution Core AI Learning"),
            ("/tenant/multi-tenant-registry", "Multi-Tenant Architecture"),
            ("/compliance/audit-trail", "Immutable Audit Trail"),
            ("/automation/intelligent-workflows", "AI-Powered Workflows"),
            ("/analytics/predictive-insights", "Predictive Business Analytics"),
            ("/optimization/recipe-suggestions", "AI Recipe Optimization"),
            ("/efficiency/billing-shortcuts", "Smart Billing System")
        ]
        
        for endpoint, feature_name in unique_features:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=15)
                
                if response.status_code == 200:
                    self.log_test(f"Unique Feature: {feature_name}", True, "Available and functional")
                elif response.status_code == 404:
                    self.log_test(f"Unique Feature: {feature_name}", False, "Not implemented")
                else:
                    self.log_test(f"Unique Feature: {feature_name}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Unique Feature: {feature_name}", False, error=e)

    def test_phoenix_protocols(self):
        """Test Phoenix Protocols self-healing system"""
        print("=" * 60)
        print("TESTING PHOENIX PROTOCOLS SELF-HEALING")
        print("=" * 60)
        
        try:
            # Test healing status
            response = self.session.get(f"{self.base_url}/phoenix/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Phoenix Status", True, "Self-healing system active")
            else:
                self.log_test("Phoenix Status", False, "System not responding")
                
            # Test healing capabilities by accessing healing stats
            response = self.session.get(f"{self.base_url}/phoenix/healing-stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Phoenix Statistics", True, "Healing stats available")
            else:
                self.log_test("Phoenix Statistics", False, "Stats not available")
                
        except Exception as e:
            self.log_test("Phoenix Protocols", False, error=e)

    def test_evolution_core(self):
        """Test Evolution Core learning system"""
        print("=" * 60)
        print("TESTING EVOLUTION CORE LEARNING SYSTEM")
        print("=" * 60)
        
        try:
            # Test learning metrics
            response = self.session.get(f"{self.base_url}/evolution/metrics", timeout=10)
            if response.status_code == 200:
                metrics = response.json()
                self.log_test("Evolution Metrics", True, "Learning metrics available")
            else:
                self.log_test("Evolution Metrics", False, "Metrics not available")
                
            # Test interaction recording
            interaction_data = {
                "user_query": "Test learning interaction",
                "ai_response": "Test response for learning",
                "rating": 5
            }
            
            response = self.session.post(f"{self.base_url}/evolution/record-interaction", 
                                       json=interaction_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                interaction_id = result.get("interaction_id")
                self.log_test("Evolution Learning", True, f"Interaction recorded: {interaction_id}")
            else:
                self.log_test("Evolution Learning", False, "Learning not functional")
                
        except Exception as e:
            self.log_test("Evolution Core", False, error=e)

    def test_streaming_capabilities(self):
        """Test real-time streaming capabilities"""
        print("=" * 60)
        print("TESTING STREAMING CAPABILITIES")
        print("=" * 60)
        
        try:
            stream_data = {
                "message": "Stream me real-time business insights",
                "stream": True
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/stream",
                json=stream_data,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                chunks_received = 0
                total_content = ""
                
                for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                    if chunk:
                        chunks_received += 1
                        total_content += str(chunk)
                        if chunks_received >= 5:  # Test streaming works
                            break
                
                self.log_test("Streaming Capabilities", chunks_received > 0, 
                            f"Chunks: {chunks_received}, Content: {len(total_content)} chars")
            else:
                self.log_test("Streaming Capabilities", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Streaming Capabilities", False, error=e)

    def test_data_pipeline(self):
        """Test data sync and pipeline operations"""
        print("=" * 60)
        print("TESTING DATA PIPELINE")
        print("=" * 60)
        
        pipeline_endpoints = [
            ("/data/sync-status", "Data Sync Status"),
            ("/data/quality-score", "Data Quality Assessment"),
            ("/data/recent-syncs", "Recent Sync Operations"),
            ("/bigquery/connection", "BigQuery Connection")
        ]
        
        for endpoint, name in pipeline_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=15)
                
                if response.status_code == 200:
                    self.log_test(name, True, "Pipeline operational")
                elif response.status_code == 404:
                    self.log_test(name, False, "Endpoint not available")
                else:
                    self.log_test(name, False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(name, False, error=e)

    def run_comprehensive_test(self):
        """Execute complete 360-degree testing suite"""
        start_time = time.time()
        
        print("TITAN 360 DEGREE COMPREHENSIVE TESTING SUITE")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Testing proactive AI business intelligence capabilities...")
        print()
        
        # Execute all test suites
        self.test_titan_ai_intelligence()
        self.test_reports_generation()
        self.test_proactive_monitoring()
        self.test_authentication_system()
        self.test_unique_erp_features()
        self.test_phoenix_protocols()
        self.test_evolution_core()
        self.test_streaming_capabilities()
        self.test_data_pipeline()
        
        # Generate comprehensive summary
        self.generate_final_report(time.time() - start_time)

    def generate_final_report(self, total_time):
        """Generate final comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("=" * 60)
        print("TITAN 360 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        print(f"Total Tests Executed: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Test Time: {total_time:.1f} seconds")
        print()
        
        # Critical system assessment
        if success_rate >= 80:
            print("TITAN SYSTEM STATUS: PRODUCTION READY")
            print("All critical systems operational with advanced AI capabilities")
        elif success_rate >= 60:
            print("TITAN SYSTEM STATUS: NEEDS MINOR FIXES")
            print("Core systems working, some features need attention")
        else:
            print("TITAN SYSTEM STATUS: REQUIRES MAJOR FIXES")
            print("Multiple critical systems need immediate attention")
        
        print()
        
        # Failed tests summary
        if failed_tests > 0:
            print("FAILED TESTS REQUIRING ATTENTION:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result.get('error', result.get('details', 'Unknown issue'))}")
        
        print()
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

if __name__ == "__main__":
    tester = Titan360Tester()
    tester.run_comprehensive_test()
