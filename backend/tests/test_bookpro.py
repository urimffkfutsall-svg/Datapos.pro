"""
BookPRO Backend API Tests
Tests for: Authentication, Services, Clients, Staff, Appointments, Dashboard, Tenants
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN = {"username": "urimi1806", "password": "1806"}
SALON_ADMIN = {"username": "salon_admin", "password": "admin123"}
STYLIST = {"username": "stiliste1", "password": "stil123"}


class TestBookPROAuth:
    """Authentication endpoint tests"""
    
    def test_super_admin_login(self):
        """Test super admin login"""
        response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=SUPER_ADMIN)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["username"] == SUPER_ADMIN["username"]
        print(f"✓ Super admin login successful: {data['user']['username']}")
    
    def test_salon_admin_login(self):
        """Test salon admin login"""
        response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=SALON_ADMIN)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["username"] == SALON_ADMIN["username"]
        print(f"✓ Salon admin login successful: {data['user']['username']}")
    
    def test_stylist_login(self):
        """Test stylist login"""
        response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=STYLIST)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "stylist"
        print(f"✓ Stylist login successful: {data['user']['username']}")
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")
    
    def test_get_me_endpoint(self):
        """Test /me endpoint"""
        # Login first
        login_resp = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=SALON_ADMIN)
        token = login_resp.json()["access_token"]
        
        # Get user info
        response = requests.get(
            f"{BASE_URL}/api/bookpro/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == SALON_ADMIN["username"]
        print(f"✓ /me endpoint working: {data['username']}")


@pytest.fixture
def admin_token():
    """Get salon admin token"""
    response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=SALON_ADMIN)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Salon admin login failed")


@pytest.fixture
def super_admin_token():
    """Get super admin token"""
    response = requests.post(f"{BASE_URL}/api/bookpro/auth/login", json=SUPER_ADMIN)
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Super admin login failed")


class TestBookPROServices:
    """Services CRUD tests"""
    
    def test_get_services(self, admin_token):
        """Test getting all services"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} services")
        
        # Verify service structure
        if len(data) > 0:
            service = data[0]
            assert "id" in service
            assert "name" in service
            assert "price" in service
            assert "duration_minutes" in service
    
    def test_create_service(self, admin_token):
        """Test creating a new service"""
        service_data = {
            "name": "TEST_Prerje Speciale",
            "category": "haircut",
            "description": "Test service for automated testing",
            "duration_minutes": 45,
            "price": 25.0,
            "deposit_required": False,
            "is_popular": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == service_data["name"]
        assert data["price"] == service_data["price"]
        assert data["duration_minutes"] == service_data["duration_minutes"]
        print(f"✓ Created service: {data['name']} (ID: {data['id']})")
        
        # Cleanup - delete the test service
        delete_resp = requests.delete(
            f"{BASE_URL}/api/bookpro/services/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_resp.status_code == 200
        print(f"✓ Cleaned up test service")
    
    def test_update_service(self, admin_token):
        """Test updating a service"""
        # First create a service
        service_data = {
            "name": "TEST_Update Service",
            "category": "haircut",
            "duration_minutes": 30,
            "price": 20.0
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        service_id = create_resp.json()["id"]
        
        # Update the service
        update_data = {
            "name": "TEST_Updated Service Name",
            "price": 30.0
        }
        
        response = requests.put(
            f"{BASE_URL}/api/bookpro/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        print(f"✓ Updated service: {data['name']}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/bookpro/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_delete_service(self, admin_token):
        """Test deleting (deactivating) a service"""
        # Create a service to delete
        service_data = {
            "name": "TEST_Delete Service",
            "category": "haircut",
            "duration_minutes": 30,
            "price": 15.0
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=service_data
        )
        service_id = create_resp.json()["id"]
        
        # Delete the service
        response = requests.delete(
            f"{BASE_URL}/api/bookpro/services/{service_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "sukses" in response.json()["message"].lower() or "çaktivizua" in response.json()["message"].lower()
        print(f"✓ Deleted service: {service_id}")


class TestBookPROClients:
    """Clients CRUD tests"""
    
    def test_get_clients(self, admin_token):
        """Test getting all clients"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/clients",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} clients")
        
        if len(data) > 0:
            client = data[0]
            assert "id" in client
            assert "full_name" in client
            assert "phone" in client
    
    def test_create_client(self, admin_token):
        """Test creating a new client"""
        client_data = {
            "full_name": "TEST_Maria Testi",
            "phone": "+383441234567",
            "email": "test.maria@example.com",
            "gender": "female",
            "notes": "Test client for automated testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookpro/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=client_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["full_name"] == client_data["full_name"]
        assert data["phone"] == client_data["phone"]
        print(f"✓ Created client: {data['full_name']} (ID: {data['id']})")
        
        # Cleanup
        delete_resp = requests.delete(
            f"{BASE_URL}/api/bookpro/clients/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_resp.status_code == 200
        print(f"✓ Cleaned up test client")
    
    def test_update_client(self, admin_token):
        """Test updating a client"""
        # Create a client first
        client_data = {
            "full_name": "TEST_Update Client",
            "phone": "+383449876543"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=client_data
        )
        client_id = create_resp.json()["id"]
        
        # Update the client
        update_data = {
            "full_name": "TEST_Updated Client Name",
            "email": "updated@example.com"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/bookpro/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["email"] == update_data["email"]
        print(f"✓ Updated client: {data['full_name']}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/bookpro/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_delete_client(self, admin_token):
        """Test deleting a client"""
        # Create a client to delete
        client_data = {
            "full_name": "TEST_Delete Client",
            "phone": "+383441112222"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/clients",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=client_data
        )
        client_id = create_resp.json()["id"]
        
        # Delete the client
        response = requests.delete(
            f"{BASE_URL}/api/bookpro/clients/{client_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "sukses" in response.json()["message"].lower() or "fshi" in response.json()["message"].lower()
        print(f"✓ Deleted client: {client_id}")
    
    def test_search_clients(self, admin_token):
        """Test searching clients"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/clients?search=Ana",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Search returned {len(data)} clients")


class TestBookPROStaff:
    """Staff CRUD tests"""
    
    def test_get_staff(self, admin_token):
        """Test getting all staff"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} staff members")
        
        if len(data) > 0:
            staff = data[0]
            assert "id" in staff
            assert "full_name" in staff
            assert "role" in staff
    
    def test_create_staff(self, admin_token):
        """Test creating a new staff member"""
        import time
        unique_id = str(int(time.time()))
        staff_data = {
            "username": f"test_stiliste_{unique_id}",
            "password": "test123",
            "full_name": "TEST_Stiliste Auto",
            "role": "stylist",
            "phone": "+383441234999",
            "email": f"test.stiliste{unique_id}@example.com",
            "specializations": ["haircut", "coloring"],
            "commission_percent": 30
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=staff_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["full_name"] == staff_data["full_name"]
        assert data["role"] == staff_data["role"]
        print(f"✓ Created staff: {data['full_name']} (ID: {data['id']})")
        
        # Cleanup
        delete_resp = requests.delete(
            f"{BASE_URL}/api/bookpro/staff/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_resp.status_code == 200
        print(f"✓ Cleaned up test staff")
    
    def test_update_staff(self, admin_token):
        """Test updating a staff member"""
        import time
        unique_id = str(int(time.time()))
        # Create staff first
        staff_data = {
            "username": f"test_update_staff_{unique_id}",
            "password": "test123",
            "full_name": "TEST_Update Staff",
            "role": "stylist"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=staff_data
        )
        staff_id = create_resp.json()["id"]
        
        # Update the staff
        update_data = {
            "full_name": "TEST_Updated Staff Name",
            "commission_percent": 35
        }
        
        response = requests.put(
            f"{BASE_URL}/api/bookpro/staff/{staff_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        print(f"✓ Updated staff: {data['full_name']}")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/bookpro/staff/{staff_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_delete_staff(self, admin_token):
        """Test deleting (deactivating) a staff member"""
        import time
        unique_id = str(int(time.time()))
        # Create staff to delete
        staff_data = {
            "username": f"test_delete_staff_{unique_id}",
            "password": "test123",
            "full_name": "TEST_Delete Staff",
            "role": "stylist"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=staff_data
        )
        staff_id = create_resp.json()["id"]
        
        # Delete the staff
        response = requests.delete(
            f"{BASE_URL}/api/bookpro/staff/{staff_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print(f"✓ Deleted staff: {staff_id}")


class TestBookPROAppointments:
    """Appointments CRUD tests"""
    
    def test_get_appointments(self, admin_token):
        """Test getting appointments"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/bookpro/appointments?date={today}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} appointments for today")
    
    def test_get_today_appointments(self, admin_token):
        """Test getting today's appointments"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/appointments/today",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} appointments for today")
    
    def test_create_appointment(self, admin_token):
        """Test creating a new appointment"""
        # First get a stylist
        staff_resp = requests.get(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff = staff_resp.json()
        if not staff:
            pytest.skip("No staff available for appointment test")
        
        stylist_id = staff[0]["id"]
        
        # Get a service
        services_resp = requests.get(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        services = services_resp.json()
        if not services:
            pytest.skip("No services available for appointment test")
        
        service = services[0]
        
        # Create appointment for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        appointment_data = {
            "client_name": "TEST_Appointment Client",
            "client_phone": "+383441234888",
            "stylist_id": stylist_id,
            "services": [{
                "service_id": service["id"],
                "service_name": service["name"],
                "price": service["price"],
                "duration_minutes": service["duration_minutes"]
            }],
            "appointment_date": tomorrow,
            "start_time": "10:00",
            "notes": "Test appointment",
            "source": "phone"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookpro/appointments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=appointment_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["client_name"] == appointment_data["client_name"]
        assert data["appointment_date"] == tomorrow
        assert data["status"] == "confirmed"
        print(f"✓ Created appointment: {data['appointment_number']} (ID: {data['id']})")
        
        # Cleanup - cancel the appointment
        cancel_resp = requests.post(
            f"{BASE_URL}/api/bookpro/appointments/{data['id']}/cancel",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert cancel_resp.status_code == 200
        print(f"✓ Cleaned up test appointment")
    
    def test_complete_appointment(self, admin_token):
        """Test completing an appointment"""
        import time
        # First get a stylist
        staff_resp = requests.get(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff = staff_resp.json()
        if not staff:
            pytest.skip("No staff available")
        
        stylist_id = staff[0]["id"]
        
        # Get a service
        services_resp = requests.get(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        services = services_resp.json()
        if not services:
            pytest.skip("No services available")
        
        service = services[0]
        
        # Create appointment for today with unique time
        today = datetime.now().strftime("%Y-%m-%d")
        unique_hour = 15 + (int(time.time()) % 4)  # 15-18 range
        
        appointment_data = {
            "client_name": "TEST_Complete Client",
            "client_phone": "+383441234777",
            "stylist_id": stylist_id,
            "services": [{
                "service_id": service["id"],
                "service_name": service["name"],
                "price": service["price"],
                "duration_minutes": service["duration_minutes"]
            }],
            "appointment_date": today,
            "start_time": f"{unique_hour}:00",
            "source": "walk_in"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/appointments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=appointment_data
        )
        
        if create_resp.status_code != 200:
            pytest.skip(f"Could not create appointment: {create_resp.text}")
        
        appointment_id = create_resp.json()["id"]
        
        # Complete the appointment
        response = requests.post(
            f"{BASE_URL}/api/bookpro/appointments/{appointment_id}/complete?payment_method=cash&tip_amount=5",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "sukses" in data["message"].lower() or "përfundua" in data["message"].lower()
        print(f"✓ Completed appointment: {appointment_id}")
    
    def test_cancel_appointment(self, admin_token):
        """Test cancelling an appointment"""
        # First get a stylist
        staff_resp = requests.get(
            f"{BASE_URL}/api/bookpro/staff",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff = staff_resp.json()
        if not staff:
            pytest.skip("No staff available")
        
        stylist_id = staff[0]["id"]
        
        # Get a service
        services_resp = requests.get(
            f"{BASE_URL}/api/bookpro/services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        services = services_resp.json()
        if not services:
            pytest.skip("No services available")
        
        service = services[0]
        
        # Create appointment
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        appointment_data = {
            "client_name": "TEST_Cancel Client",
            "client_phone": "+383441234666",
            "stylist_id": stylist_id,
            "services": [{
                "service_id": service["id"],
                "service_name": service["name"],
                "price": service["price"],
                "duration_minutes": service["duration_minutes"]
            }],
            "appointment_date": tomorrow,
            "start_time": "11:00",
            "source": "phone"
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/appointments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=appointment_data
        )
        appointment_id = create_resp.json()["id"]
        
        # Cancel the appointment
        response = requests.post(
            f"{BASE_URL}/api/bookpro/appointments/{appointment_id}/cancel?reason=Test%20cancellation",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "anulua" in response.json()["message"].lower()
        print(f"✓ Cancelled appointment: {appointment_id}")
    
    def test_get_calendar_view(self, admin_token):
        """Test calendar view endpoint"""
        today = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/bookpro/appointments/calendar?start_date={today}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Calendar view returned data for {len(data)} days")


class TestBookPRODashboard:
    """Dashboard and statistics tests"""
    
    def test_get_dashboard_stats(self, admin_token):
        """Test getting dashboard statistics"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/dashboard/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "today_appointments" in data
        assert "today_revenue" in data
        assert "week_appointments" in data
        assert "week_revenue" in data
        assert "month_appointments" in data
        assert "month_revenue" in data
        assert "total_clients" in data
        print(f"✓ Dashboard stats: Today={data['today_appointments']} appointments, Revenue={data['today_revenue']}€")
    
    def test_get_revenue_chart(self, admin_token):
        """Test revenue chart endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/dashboard/revenue-chart?period=week",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Revenue chart returned {len(data)} data points")
    
    def test_get_top_services(self, admin_token):
        """Test top services endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/dashboard/top-services",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Top services returned {len(data)} services")
    
    def test_get_top_stylists(self, admin_token):
        """Test top stylists endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/dashboard/top-stylists",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Top stylists returned {len(data)} stylists")


class TestBookPROTenants:
    """Tenant management tests (Super Admin only)"""
    
    def test_get_tenants(self, super_admin_token):
        """Test getting all tenants"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} tenants")
        
        if len(data) > 0:
            tenant = data[0]
            assert "id" in tenant
            assert "salon_name" in tenant
            assert "status" in tenant
    
    def test_create_tenant(self, super_admin_token):
        """Test creating a new tenant"""
        tenant_data = {
            "name": "test_salon_auto",
            "salon_name": "TEST_Salloni Auto",
            "email": "test.salon@example.com",
            "phone": "+383441234555",
            "address": "Test Address 123",
            "city": "Prishtinë",
            "admin_username": "test_salon_admin_auto",
            "admin_password": "test123",
            "admin_full_name": "Test Admin Auto",
            "subscription_months": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bookpro/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json=tenant_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["salon_name"] == tenant_data["salon_name"]
        assert data["status"] == "active"
        print(f"✓ Created tenant: {data['salon_name']} (ID: {data['id']})")
        
        # Cleanup - delete the tenant
        delete_resp = requests.delete(
            f"{BASE_URL}/api/bookpro/tenants/{data['id']}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert delete_resp.status_code == 200
        print(f"✓ Cleaned up test tenant")
    
    def test_delete_tenant(self, super_admin_token):
        """Test deleting a tenant"""
        # Create a tenant to delete
        tenant_data = {
            "name": "test_delete_salon",
            "salon_name": "TEST_Delete Salon",
            "email": "delete.salon@example.com",
            "phone": "+383441234444",
            "admin_username": "test_delete_admin",
            "admin_password": "test123",
            "admin_full_name": "Delete Admin",
            "subscription_months": 1
        }
        
        create_resp = requests.post(
            f"{BASE_URL}/api/bookpro/tenants",
            headers={"Authorization": f"Bearer {super_admin_token}"},
            json=tenant_data
        )
        tenant_id = create_resp.json()["id"]
        
        # Delete the tenant
        response = requests.delete(
            f"{BASE_URL}/api/bookpro/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        assert "sukses" in response.json()["message"].lower() or "fshi" in response.json()["message"].lower()
        print(f"✓ Deleted tenant: {tenant_id}")
    
    def test_tenant_access_denied_for_non_super_admin(self, admin_token):
        """Test that non-super admin cannot access tenant endpoints"""
        response = requests.get(
            f"{BASE_URL}/api/bookpro/tenants",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 403
        print("✓ Tenant access correctly denied for non-super admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
