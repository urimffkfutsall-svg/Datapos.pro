"""
PhoneSoftware Backend API Tests
Tests for: Authentication, Repairs, Public Status, Role-based Access
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDS = {"username": "test_admin", "password": "admin123"}
WORKER_CREDS = {"username": "test_worker", "password": "worker123"}
SUPERADMIN_CREDS = {"username": "urimi1806", "password": "1806"}


class TestPhoneSoftwareAuth:
    """Authentication tests for PhoneSoftware"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["username"] == "test_admin"
    
    def test_worker_login_success(self):
        """Test worker login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=WORKER_CREDS
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "worker"
        assert data["user"]["username"] == "test_worker"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json={"username": "invalid", "password": "invalid"}
        )
        assert response.status_code == 401


class TestPhoneSoftwareRepairs:
    """Repair CRUD tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def worker_token(self):
        """Get worker auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=WORKER_CREDS
        )
        return response.json()["access_token"]
    
    def test_get_repairs_as_admin(self, admin_token):
        """Test getting repairs list as admin"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/repairs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_repairs_as_worker(self, worker_token):
        """Test getting repairs list as worker"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/repairs",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_repair_with_manual_customer(self, admin_token):
        """Test creating repair with manual customer data (not from existing customers)"""
        repair_data = {
            "customer_name": "TEST_Manual Customer",
            "customer_phone": "+383 44 123 456",
            "device_type": "phone",
            "brand": "Samsung",
            "model": "Galaxy S24",
            "imei": "123456789012345",
            "color": "Black",
            "problem_description": "Screen cracked - TEST repair",
            "estimated_cost": 50.0,
            "warranty_months": 3
        }
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ticket_number" in data
        assert data["ticket_number"].startswith("REP-")
        assert data["customer_name"] == "TEST_Manual Customer"
        assert data["customer_phone"] == "+383 44 123 456"
        assert data["status"] == "received"
        assert data["brand"] == "Samsung"
        assert data["model"] == "Galaxy S24"
        
        # Store for cleanup
        self.__class__.created_repair_id = data["id"]
        self.__class__.created_ticket_number = data["ticket_number"]
        return data
    
    def test_create_repair_without_customer(self, admin_token):
        """Test creating repair without any customer info (optional customer)"""
        repair_data = {
            "device_type": "phone",
            "brand": "Apple",
            "model": "iPhone 15",
            "problem_description": "Battery replacement - TEST repair no customer"
        }
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ticket_number" in data
        assert data["customer_name"] is None or data["customer_name"] == ""
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_get_repair_by_id(self, admin_token):
        """Test getting single repair by ID"""
        # First create a repair
        repair_data = {
            "brand": "Xiaomi",
            "model": "14 Pro",
            "problem_description": "TEST get by id"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair_id = create_response.json()["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == repair_id
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_update_repair_status(self, admin_token):
        """Test updating repair status through workflow"""
        # Create repair
        repair_data = {
            "brand": "OnePlus",
            "model": "12",
            "problem_description": "TEST status update"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair = create_response.json()
        repair_id = repair["id"]
        
        # Verify initial status is 'received'
        assert repair["status"] == "received"
        
        # Update to 'in_progress'
        update_response = requests.put(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            json={"status": "in_progress"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "in_progress"
        
        # Update to 'completed'
        update_response = requests.put(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            json={"status": "completed", "labor_cost": 30.0},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        
        # Update to 'delivered'
        update_response = requests.put(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            json={"status": "delivered"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "delivered"
        assert data["delivered_at"] is not None
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_update_repair_to_cannot_repair(self, admin_token):
        """Test updating repair to 'cannot_repair' status"""
        # Create repair
        repair_data = {
            "brand": "Huawei",
            "model": "P60",
            "problem_description": "TEST cannot repair status"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair_id = create_response.json()["id"]
        
        # Update to 'cannot_repair'
        update_response = requests.put(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            json={"status": "cannot_repair", "diagnosis": "Water damage beyond repair"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "cannot_repair"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_repair_stats(self, admin_token):
        """Test repair statistics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/repairs/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "status_counts" in data
        assert "today_count" in data
        assert "week_count" in data
    
    def test_worker_cannot_delete_repair(self, worker_token, admin_token):
        """Test that worker role cannot delete repairs"""
        # Create repair as admin
        repair_data = {
            "brand": "Google",
            "model": "Pixel 8",
            "problem_description": "TEST worker delete restriction"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair_id = create_response.json()["id"]
        
        # Try to delete as worker - should fail
        delete_response = requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert delete_response.status_code == 403
        
        # Cleanup as admin
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPhoneSoftwarePublicEndpoints:
    """Public endpoints tests (no auth required)"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    def test_public_repair_status(self, admin_token):
        """Test public repair status endpoint"""
        # Create a repair first
        repair_data = {
            "customer_name": "TEST_Public Status Customer",
            "customer_phone": "+383 44 999 888",
            "brand": "Sony",
            "model": "Xperia 1 V",
            "problem_description": "TEST public status check"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair = create_response.json()
        ticket_number = repair["ticket_number"]
        
        # Check public status (no auth)
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/public/repair-status/{ticket_number}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_number"] == ticket_number
        assert data["status"] == "received"
        assert data["status_label"] == "Pranuar në servis"
        assert "device" in data
        assert "shop" in data
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_public_repair_status_not_found(self):
        """Test public status with invalid ticket number"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/public/repair-status/REP-INVALID-0000"
        )
        assert response.status_code == 404
    
    def test_qr_code_generation(self, admin_token):
        """Test QR code generation endpoint"""
        # Create a repair first
        repair_data = {
            "brand": "Motorola",
            "model": "Edge 40",
            "problem_description": "TEST QR code generation"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair = create_response.json()
        ticket_number = repair["ticket_number"]
        
        # Get QR code image
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/public/qr/{ticket_number}"
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_qr_code_base64(self, admin_token):
        """Test QR code base64 endpoint"""
        # Create a repair first
        repair_data = {
            "brand": "Asus",
            "model": "ROG Phone 8",
            "problem_description": "TEST QR base64"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair = create_response.json()
        ticket_number = repair["ticket_number"]
        
        # Get QR code as base64
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/public/qr-base64/{ticket_number}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_receipt_data(self, admin_token):
        """Test receipt data endpoint for printing"""
        # Create a repair first
        repair_data = {
            "customer_name": "TEST_Receipt Customer",
            "customer_phone": "+383 44 777 666",
            "brand": "Nothing",
            "model": "Phone 2",
            "problem_description": "TEST receipt data",
            "estimated_cost": 45.0,
            "warranty_months": 2,
            "accessories_received": ["Charger", "Case"]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair = create_response.json()
        ticket_number = repair["ticket_number"]
        
        # Get receipt data
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/public/receipt-data/{ticket_number}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_number"] == ticket_number
        assert data["customer_name"] == "TEST_Receipt Customer"
        assert data["customer_phone"] == "+383 44 777 666"
        assert data["brand"] == "Nothing"
        assert data["model"] == "Phone 2"
        assert "qr_code" in data
        assert "status_url" in data
        assert "shop" in data
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPhoneSoftwareRepairStatuses:
    """Test all repair status values"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    def test_all_status_values_available(self, admin_token):
        """Verify all required statuses are available: received, in_progress, completed, cannot_repair, delivered"""
        # Create repair
        repair_data = {
            "brand": "TEST",
            "model": "Status Test",
            "problem_description": "TEST all statuses"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/phonesoftware/repairs",
            json=repair_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        repair_id = create_response.json()["id"]
        
        # Test each status
        statuses = ["received", "in_progress", "completed", "cannot_repair", "delivered"]
        
        for status in statuses:
            update_response = requests.put(
                f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
                json={"status": status},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert update_response.status_code == 200, f"Failed to set status to {status}"
            assert update_response.json()["status"] == status
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/phonesoftware/repairs/{repair_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )


class TestPhoneSoftwareDashboard:
    """Dashboard and reports tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def worker_token(self):
        """Get worker auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=WORKER_CREDS
        )
        return response.json()["access_token"]
    
    def test_dashboard_as_admin(self, admin_token):
        """Test dashboard endpoint as admin"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/reports/dashboard",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "repairs" in data
        assert "revenue" in data
    
    def test_dashboard_as_worker(self, worker_token):
        """Test dashboard endpoint as worker"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/reports/dashboard",
            headers={"Authorization": f"Bearer {worker_token}"}
        )
        assert response.status_code == 200


class TestPhoneSoftwareCustomers:
    """Customer management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    def test_get_customers(self, admin_token):
        """Test getting customers list"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/customers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPhoneSoftwareStaff:
    """Staff management tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/phonesoftware/auth/login",
            json=ADMIN_CREDS
        )
        return response.json()["access_token"]
    
    def test_get_technicians(self, admin_token):
        """Test getting technicians list"""
        response = requests.get(
            f"{BASE_URL}/api/phonesoftware/staff/technicians",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
