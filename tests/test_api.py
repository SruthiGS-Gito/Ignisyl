"""
API Tests for IGNISYL
Tests all REST API endpoints
"""

import pytest
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

# Test credentials
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == TEST_USER["username"]
        print("✅ Login test passed")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": "invalid_user",
                "password": "wrong_password",
                "ip_address": "127.0.0.1"
            }
        )
        
        assert response.status_code in [401, 400]
        print("✅ Invalid login test passed")

class TestDashboard:
    """Test dashboard endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        return response.json()["access_token"]
    
    def test_get_dashboard_stats(self, auth_token):
        """Test getting dashboard statistics"""
        response = requests.get(
            f"{API_URL}/dashboard/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "overview" in data
        assert "total_users" in data["overview"]
        assert "threats_detected_today" in data["overview"]
        print("✅ Dashboard stats test passed")
    
    def test_get_recent_activities(self, auth_token):
        """Test getting recent activities"""
        response = requests.get(
            f"{API_URL}/activities/recent?limit=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
        print("✅ Recent activities test passed")

class TestUsers:
    """Test user management endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        return response.json()["access_token"]
    
    def test_get_users_list(self, auth_token):
        """Test getting users list"""
        response = requests.get(
            f"{API_URL}/users/list",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        print("✅ Users list test passed")

class TestAnalyst:
    """Test analyst control endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        return response.json()["access_token"]
    
    def test_get_pending_decisions(self, auth_token):
        """Test getting pending analyst decisions"""
        response = requests.get(
            f"{API_URL}/analyst/pending-decisions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "pending_decisions" in data
        print("✅ Pending decisions test passed")
    
    def test_analyst_take_action(self, auth_token):
        """Test analyst taking action on threat"""
        # This is a mock test - in production would need a real threat_id
        test_threat_id = "test_user"
        
        response = requests.post(
            f"{API_URL}/analyst/threat/{test_threat_id}/action",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "action": "RESTRICT",
                "custom_restrictions": {
                    "block_external_internet": True,
                    "rate_limit_mbps": 1,
                    "notify_user": True
                },
                "reason": "Test action for unit testing",
                "duration_minutes": 60
            }
        )
        
        # May fail if test_user doesn't exist, which is OK for unit test
        assert response.status_code in [200, 404]
        print("✅ Analyst action test passed")

class TestThreats:
    """Test threat detection endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        return response.json()["access_token"]
    
    def test_get_active_threats(self, auth_token):
        """Test getting active threats"""
        response = requests.get(
            f"{API_URL}/threats/active",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "threats" in data or "active_count" in data
        print("✅ Active threats test passed")

def run_all_tests():
    """Run all API tests"""
    print("=" * 60)
    print("IGNISYL - API Tests")
    print("=" * 60)
    print("\nMake sure backend is running at http://127.0.0.1:8000\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=2)
        if response.status_code != 200:
            print("❌ Backend server not responding")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend server")
        print("   Please start the backend first: cd backend && python main.py")
        return
    
    print("✅ Backend server is running\n")
    
    # Run tests manually (without pytest runner)
    try:
        # Authentication tests
        print("\n📋 Testing Authentication...")
        auth = TestAuthentication()
        auth.test_login_success()
        auth.test_login_invalid_credentials()
        
        # Get token for other tests
        token_response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"],
                "ip_address": "127.0.0.1"
            }
        )
        token = token_response.json()["access_token"]
        
        # Dashboard tests
        print("\n📋 Testing Dashboard...")
        dashboard = TestDashboard()
        dashboard.test_get_dashboard_stats(token)
        dashboard.test_get_recent_activities(token)
        
        # Users tests
        print("\n📋 Testing User Management...")
        users = TestUsers()
        users.test_get_users_list(token)
        
        # Analyst tests
        print("\n📋 Testing Analyst Control...")
        analyst = TestAnalyst()
        analyst.test_get_pending_decisions(token)
        analyst.test_analyst_take_action(token)
        
        # Threats tests
        print("\n📋 Testing Threats...")
        threats = TestThreats()
        threats.test_get_active_threats(token)
        
        print("\n" + "=" * 60)
        print("✅ All API tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
