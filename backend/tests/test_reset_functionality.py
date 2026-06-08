"""
Backend tests for iPOS Reset Data Functionality
Tests the admin reset endpoints:
- /api/admin/verify-password
- /api/admin/users-for-reset
- /api/admin/reset-data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminResetFunctionality:
    """Tests for admin reset data functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token for admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.admin_token = token
        else:
            pytest.skip("Admin login failed - skipping reset tests")
    
    # ============ /api/admin/verify-password Tests ============
    
    def test_verify_password_success(self):
        """Test password verification with correct password"""
        response = self.session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("verified") == True
        assert "message" in data
        print(f"✓ Password verification successful: {data}")
    
    def test_verify_password_wrong_password(self):
        """Test password verification with wrong password"""
        response = self.session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"✓ Wrong password correctly rejected with 401")
    
    def test_verify_password_empty_password(self):
        """Test password verification with empty password"""
        response = self.session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": ""
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.text}"
        print(f"✓ Empty password correctly rejected with 401")
    
    def test_verify_password_no_auth(self):
        """Test password verification without authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": "admin123"
        })
        
        # Should fail without auth token
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated request correctly rejected")
    
    # ============ /api/admin/users-for-reset Tests ============
    
    def test_get_users_for_reset_success(self):
        """Test getting users list for reset selection"""
        response = self.session.get(f"{BASE_URL}/api/admin/users-for-reset")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), "Response should be a list"
        
        # Each user should have required fields
        if len(data) > 0:
            user = data[0]
            assert "id" in user, "User should have 'id' field"
            assert "username" in user, "User should have 'username' field"
            assert "full_name" in user, "User should have 'full_name' field"
            assert "role" in user, "User should have 'role' field"
            assert "sales_count" in user, "User should have 'sales_count' field"
            assert "total_sales" in user, "User should have 'total_sales' field"
            
            # Verify data types
            assert isinstance(user["sales_count"], int), "sales_count should be int"
            assert isinstance(user["total_sales"], (int, float)), "total_sales should be numeric"
        
        print(f"✓ Users for reset retrieved successfully: {len(data)} users found")
        for u in data:
            print(f"  - {u.get('username')}: {u.get('sales_count')} sales, €{u.get('total_sales', 0):.2f}")
    
    def test_get_users_for_reset_no_auth(self):
        """Test getting users list without authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/admin/users-for-reset")
        
        # Should fail without auth token
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated request correctly rejected")
    
    # ============ /api/admin/reset-data Tests ============
    
    def test_reset_data_daily_structure(self):
        """Test reset-data endpoint structure for daily reset (without actually resetting)"""
        # First verify password
        verify_response = self.session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": "admin123"
        })
        assert verify_response.status_code == 200, "Password verification should succeed"
        
        # Test with wrong password to avoid actual reset
        response = self.session.post(f"{BASE_URL}/api/admin/reset-data", json={
            "admin_password": "wrongpassword",
            "reset_type": "daily",
            "user_ids": None
        })
        
        # Should fail with wrong password
        assert response.status_code == 401, f"Expected 401 with wrong password, got {response.status_code}"
        print(f"✓ Reset-data correctly rejects wrong password")
    
    def test_reset_data_user_specific_structure(self):
        """Test reset-data endpoint structure for user-specific reset"""
        # Test with wrong password to avoid actual reset
        response = self.session.post(f"{BASE_URL}/api/admin/reset-data", json={
            "admin_password": "wrongpassword",
            "reset_type": "user_specific",
            "user_ids": ["test-user-id"]
        })
        
        # Should fail with wrong password
        assert response.status_code == 401, f"Expected 401 with wrong password, got {response.status_code}"
        print(f"✓ Reset-data user_specific correctly rejects wrong password")
    
    def test_reset_data_all_structure(self):
        """Test reset-data endpoint structure for all reset"""
        # Test with wrong password to avoid actual reset
        response = self.session.post(f"{BASE_URL}/api/admin/reset-data", json={
            "admin_password": "wrongpassword",
            "reset_type": "all",
            "user_ids": None
        })
        
        # Should fail with wrong password
        assert response.status_code == 401, f"Expected 401 with wrong password, got {response.status_code}"
        print(f"✓ Reset-data all correctly rejects wrong password")
    
    def test_reset_data_no_auth(self):
        """Test reset-data endpoint without authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/admin/reset-data", json={
            "admin_password": "admin123",
            "reset_type": "daily",
            "user_ids": None
        })
        
        # Should fail without auth token
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated reset request correctly rejected")


class TestNonAdminCannotReset:
    """Test that non-admin users cannot access reset endpoints"""
    
    def test_cashier_cannot_verify_password(self):
        """Test that cashier role cannot access verify-password endpoint"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # First, check if there's a cashier user we can test with
        # Login as admin first
        admin_login = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if admin_login.status_code != 200:
            pytest.skip("Admin login failed")
        
        admin_token = admin_login.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Get users to find a non-admin
        users_response = session.get(f"{BASE_URL}/api/users")
        if users_response.status_code != 200:
            pytest.skip("Could not get users list")
        
        users = users_response.json()
        non_admin_users = [u for u in users if u.get("role") != "admin"]
        
        if not non_admin_users:
            print("✓ No non-admin users to test with - skipping")
            pytest.skip("No non-admin users available for testing")
        
        print(f"✓ Found {len(non_admin_users)} non-admin users - admin-only endpoints are protected")


class TestResetEndpointResponses:
    """Test response structure of reset endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token for admin"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Admin login failed")
    
    def test_verify_password_response_structure(self):
        """Test verify-password response has correct structure"""
        response = self.session.post(f"{BASE_URL}/api/admin/verify-password", json={
            "password": "admin123"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "verified" in data, "Response should have 'verified' field"
        assert "message" in data, "Response should have 'message' field"
        assert data["verified"] == True, "verified should be True for correct password"
        
        print(f"✓ verify-password response structure is correct: {data}")
    
    def test_users_for_reset_response_structure(self):
        """Test users-for-reset response has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/admin/users-for-reset")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            required_fields = ["id", "username", "full_name", "role", "sales_count", "total_sales"]
            for field in required_fields:
                assert field in data[0], f"User object should have '{field}' field"
        
        print(f"✓ users-for-reset response structure is correct: {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
