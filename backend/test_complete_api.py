"""
COMPLETE API TESTING SUITE
Automatically discovers and tests ALL 34 endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

class CompleteTester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        
    def discover_endpoints(self):
        """Auto-discover all endpoints from OpenAPI schema"""
        response = requests.get(f"{BASE_URL}/openapi.json")
        schema = response.json()
        
        endpoints = []
        for path, methods in schema["paths"].items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "summary": details.get("summary", ""),
                        "operationId": details.get("operationId", ""),
                        "parameters": details.get("parameters", [])
                    })
        
        return sorted(endpoints, key=lambda x: x["path"])
    
    def get_test_data(self, path, method):
        """Generate appropriate test data for each endpoint"""
        
        # Path parameter replacements
        test_path = path
        test_path = test_path.replace("{user_id}", "user_john.doe")
        test_path = test_path.replace("{threat_id}", "user_john.doe")
        test_path = test_path.replace("{filename}", "report.pdf")
        
        # POST/PUT data
        data = None
        if method in ["POST", "PUT"]:
            if "/simulate" in path:
                data = {"count": 5}
            elif "/firewall" in path:
                data = {"user_id": "user_john.doe", "action": "ALLOW", "duration_minutes": 30}
            elif "/register" in path:
                data = {
                    "username": "test.user",
                    "full_name": "Test User",
                    "department": "Testing",
                    "role": "Tester",
                    "email": "test@test.com"
                }
            elif "/login" in path:
                data = {"username": "admin", "password": "admin123"}
            elif "/contact-user" in path:
                data = {"message": "Test message", "method": "notification"}
            elif "/escalate" in path:
                data = {"escalate_to": "admin", "notes": "Test escalation"}
            elif "/action" in path and "/analyst" in path:
                data = {
                    "action": "RESTRICT",
                    "custom_restrictions": {"duration_minutes": 30},
                    "reason": "Testing"
                }
            elif "/broadcast" in path:
                data = {"threat_id": "test_threat", "message": "Test broadcast"}
            elif "/acknowledge" in path:
                data = {"alert_id": "test_alert", "reviewer": "admin"}
            elif "/analyze" in path:
                data = {"user_id": "user_john.doe", "activity_type": "file_access"}
            elif "/reports/user" in path:
                data = {"user_id": "user_john.doe"}
            elif "/reports/system" in path:
                data = {}
            elif "/monitoring/file-access" in path:
                data = {"user_id": "user_john.doe", "file_path": "test.txt"}
            elif "/monitoring/login" in path:
                data = {"user_id": "user_john.doe", "success": True}
            else:
                data = {}
        
        return test_path, data
    
    def test_endpoint(self, endpoint):
        """Test a single endpoint"""
        method = endpoint["method"]
        path = endpoint["path"]
        summary = endpoint["summary"]
        
        test_path, data = self.get_test_data(path, method)
        url = f"{BASE_URL}{test_path}"
        
        # Skip auth-required endpoints without proper auth
        skip_endpoints = []  # Add endpoints to skip if needed
        
        if path in skip_endpoints:
            print(f"{YELLOW}⊘{RESET} {method:6} {path:50} - SKIPPED (Requires auth)")
            self.skipped += 1
            return
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                print(f"{YELLOW}⊘{RESET} {method:6} {path:50} - SKIPPED (Unknown method)")
                self.skipped += 1
                return
            
            status = response.status_code
            time_taken = response.elapsed.total_seconds()
            
            result = {
                "endpoint": path,
                "method": method,
                "summary": summary,
                "status": status,
                "time": time_taken,
                "success": 200 <= status < 400
            }
            
            if 200 <= status < 400:
                self.passed += 1
                print(f"{GREEN}✓{RESET} {method:6} {path:50} - {status} ({time_taken:.3f}s)")
            else:
                self.failed += 1
                error_msg = response.text[:100] if response.text else "No error message"
                print(f"{RED}✗{RESET} {method:6} {path:50} - {status}")
                print(f"       → Error: {error_msg}")
                result["error"] = error_msg
            
            self.results.append(result)
            
        except requests.exceptions.Timeout:
            self.failed += 1
            print(f"{RED}✗{RESET} {method:6} {path:50} - TIMEOUT (>10s)")
            self.results.append({
                "endpoint": path,
                "method": method,
                "summary": summary,
                "error": "Timeout after 10 seconds",
                "success": False
            })
        except Exception as e:
            self.failed += 1
            print(f"{RED}✗{RESET} {method:6} {path:50} - ERROR: {str(e)[:50]}")
            self.results.append({
                "endpoint": path,
                "method": method,
                "summary": summary,
                "error": str(e),
                "success": False
            })
    
    def categorize_results(self):
        """Organize results by category"""
        categories = {}
        for result in self.results:
            path = result["endpoint"]
            
            if "/dashboard" in path:
                cat = "Dashboard"
            elif "/users" in path:
                cat = "Users"
            elif "/activities" in path:
                cat = "Activities"
            elif "/threats" in path or "/threat" in path:
                cat = "Threats"
            elif "/analyst" in path:
                cat = "Analyst"
            elif "/firewall" in path:
                cat = "Firewall"
            elif "/reports" in path:
                cat = "Reports"
            elif "/monitoring" in path:
                cat = "Monitoring"
            elif "/ml" in path:
                cat = "ML"
            elif "/auth" in path:
                cat = "Auth"
            elif "/debug" in path:
                cat = "Debug"
            else:
                cat = "Other"
            
            if cat not in categories:
                categories[cat] = {"passed": 0, "failed": 0, "total": 0}
            
            categories[cat]["total"] += 1
            if result["success"]:
                categories[cat]["passed"] += 1
            else:
                categories[cat]["failed"] += 1
        
        return categories
    
    def print_summary(self):
        """Print detailed summary"""
        total = self.passed + self.failed + self.skipped
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 80)
        print(f"{BLUE}📊 COMPREHENSIVE TEST SUMMARY{RESET}")
        print("=" * 80)
        
        # Category breakdown
        categories = self.categorize_results()
        for cat, stats in sorted(categories.items()):
            cat_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            status_color = GREEN if cat_rate == 100 else YELLOW if cat_rate >= 70 else RED
            print(f"{cat:15} {status_color}{stats['passed']:2}/{stats['total']:2}{RESET} passed ({cat_rate:.0f}%)")
        
        print("=" * 80)
        print(f"Total Tests:    {total}")
        print(f"{GREEN}Passed:         {self.passed}{RESET}")
        print(f"{RED}Failed:         {self.failed}{RESET}")
        print(f"{YELLOW}Skipped:        {self.skipped}{RESET}")
        print(f"Pass Rate:      {pass_rate:.1f}%")
        print("=" * 80)
        
        # Save detailed report
        report_file = f"complete_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "skipped": self.skipped,
                    "pass_rate": pass_rate
                },
                "categories": categories,
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    tester = CompleteTester()
    
    print(f"{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}🧪 IGNISYL COMPLETE API TEST SUITE{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    print("🔍 Discovering all endpoints...")
    endpoints = tester.discover_endpoints()
    print(f"✅ Found {len(endpoints)} endpoints\n")
    
    print(f"{BLUE}{'=' * 80}{RESET}")
    print("🚀 Testing all endpoints...")
    print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    for endpoint in endpoints:
        tester.test_endpoint(endpoint)
    
    tester.print_summary()

if __name__ == "__main__":
    main()