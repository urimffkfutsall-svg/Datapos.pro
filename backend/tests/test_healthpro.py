"""
HealthPRO - Healthcare Institute Management System Tests
Tests for: Employee management, Overtime tracking, Visitor management
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
HP_ADMIN_CREDS = {"username": "hp_admin", "password": "admin123"}
HP_VISITOR_CREDS = {"username": "visitor1", "password": "vis123"}


class TestHealthPROAuth:
    """HealthPRO Authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["username"] == "hp_admin"
        print(f"✓ Admin login successful - role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_visitor_login(self):
        """Test visitor login (if visitor exists)"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_VISITOR_CREDS)
        # Visitor may or may not exist yet
        if response.status_code == 200:
            data = response.json()
            assert data["user"]["role"] == "visitor"
            print(f"✓ Visitor login successful - role: {data['user']['role']}")
        else:
            print(f"⚠ Visitor user not found (will be created in visitor tests)")


class TestHealthPROEmployees:
    """Employee CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed - cannot run employee tests")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_employees(self):
        """Test listing all employees"""
        response = requests.get(f"{BASE_URL}/api/healthpro/employees", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} employees")
        
        # Verify employee structure
        if len(data) > 0:
            emp = data[0]
            assert "id" in emp
            assert "first_name" in emp
            assert "last_name" in emp
            assert "role" in emp
            print(f"  First employee: {emp.get('first_name')} {emp.get('last_name')} - {emp.get('role')}")
    
    def test_create_employee_with_salary(self):
        """Test creating a new employee with salary"""
        unique_id = str(uuid.uuid4())[:8]
        employee_data = {
            "first_name": "TEST_Maria",
            "last_name": "Krasniqi",
            "username": f"test_maria_{unique_id}",
            "password": "test123",
            "email": f"maria_{unique_id}@test.com",
            "phone": "+383 44 123 456",
            "role": "nurse",
            "department": "Kujdesi Ditor",
            "position": "Infermiere Kryesore",
            "salary": 800,  # €800/month for overtime calculation
            "contract_type": "full-time"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/employees", 
                                json=employee_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["first_name"] == "TEST_Maria"
        assert data["last_name"] == "Krasniqi"
        assert data["salary"] == 800
        assert data["role"] == "nurse"
        assert "id" in data
        
        # Store for cleanup
        self.created_employee_id = data["id"]
        print(f"✓ Created employee: {data['first_name']} {data['last_name']} with salary €{data['salary']}")
        
        # Verify by GET
        get_response = requests.get(f"{BASE_URL}/api/healthpro/employees/{data['id']}", 
                                   headers=self.headers)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["salary"] == 800
        print(f"✓ Verified employee persisted with salary €{fetched['salary']}")
        
        return data["id"]
    
    def test_update_employee(self):
        """Test updating an employee"""
        # First create an employee
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/healthpro/employees", json={
            "first_name": "TEST_Update",
            "last_name": "Employee",
            "username": f"test_update_{unique_id}",
            "password": "test123",
            "role": "caregiver",
            "salary": 600
        }, headers=self.headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create employee for update test")
        
        emp_id = create_response.json()["id"]
        
        # Update the employee
        update_response = requests.put(f"{BASE_URL}/api/healthpro/employees/{emp_id}", json={
            "salary": 750,
            "department": "Kujdesi Intensiv"
        }, headers=self.headers)
        
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["salary"] == 750
        assert updated["department"] == "Kujdesi Intensiv"
        print(f"✓ Updated employee salary to €{updated['salary']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/healthpro/employees/{emp_id}", headers=self.headers)
    
    def test_delete_employee(self):
        """Test deactivating an employee"""
        # First create an employee
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/healthpro/employees", json={
            "first_name": "TEST_Delete",
            "last_name": "Employee",
            "username": f"test_delete_{unique_id}",
            "password": "test123",
            "role": "support"
        }, headers=self.headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create employee for delete test")
        
        emp_id = create_response.json()["id"]
        
        # Delete (deactivate) the employee
        delete_response = requests.delete(f"{BASE_URL}/api/healthpro/employees/{emp_id}", 
                                         headers=self.headers)
        assert delete_response.status_code == 200
        print(f"✓ Employee deactivated successfully")
    
    def test_employee_stats(self):
        """Test employee statistics endpoint"""
        response = requests.get(f"{BASE_URL}/api/healthpro/employees/stats/summary", 
                               headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "by_role" in data
        print(f"✓ Employee stats: {data['total']} total, {data['active']} active")


class TestHealthPROOvertime:
    """Overtime tracking and calculation tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token and find/create test employee"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get employees to find one with salary
        emp_response = requests.get(f"{BASE_URL}/api/healthpro/employees", headers=self.headers)
        if emp_response.status_code == 200:
            employees = emp_response.json()
            # Find employee with salary for overtime calculation
            for emp in employees:
                if emp.get("salary") and emp.get("salary") > 0:
                    self.test_employee = emp
                    break
            else:
                # Create test employee with salary
                unique_id = str(uuid.uuid4())[:8]
                create_resp = requests.post(f"{BASE_URL}/api/healthpro/employees", json={
                    "first_name": "TEST_Overtime",
                    "last_name": "Employee",
                    "username": f"test_ot_{unique_id}",
                    "password": "test123",
                    "role": "nurse",
                    "salary": 800
                }, headers=self.headers)
                if create_resp.status_code == 200:
                    self.test_employee = create_resp.json()
                else:
                    pytest.skip("Could not find or create employee with salary")
    
    def test_create_overtime_normal(self):
        """Test creating normal overtime entry and verify calculation"""
        overtime_data = {
            "employee_id": self.test_employee["id"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overtime_type": "normal",
            "hours": 3,
            "notes": "TEST - Normal overtime"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                json=overtime_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["hours"] == 3
        assert data["overtime_type"] == "normal"
        assert "calculated_pay" in data
        
        # Verify calculation: hours * (salary/176) * coefficient
        # For €800 salary: hourly_rate = 800/176 = €4.545
        # Normal coefficient = 1.25
        # Expected: 3 * 4.545 * 1.25 = €17.05 (approximately)
        salary = self.test_employee.get("salary", 800)
        hourly_rate = salary / 176
        expected_pay = round(3 * hourly_rate * 1.25, 2)
        
        assert abs(data["calculated_pay"] - expected_pay) < 0.1, \
            f"Expected ~€{expected_pay}, got €{data['calculated_pay']}"
        
        print(f"✓ Normal overtime created: {data['hours']}h = €{data['calculated_pay']}")
        print(f"  Calculation: {data['hours']} * (€{salary}/176) * 1.25 = €{expected_pay}")
        
        # Store for cleanup
        self.created_overtime_id = data["id"]
        return data["id"]
    
    def test_create_overtime_night(self):
        """Test creating night overtime (coefficient 1.5)"""
        overtime_data = {
            "employee_id": self.test_employee["id"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overtime_type": "night",
            "hours": 2,
            "notes": "TEST - Night shift overtime"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                json=overtime_data, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        salary = self.test_employee.get("salary", 800)
        hourly_rate = salary / 176
        expected_pay = round(2 * hourly_rate * 1.5, 2)
        
        assert abs(data["calculated_pay"] - expected_pay) < 0.1
        print(f"✓ Night overtime: {data['hours']}h = €{data['calculated_pay']} (x1.5)")
        
        return data["id"]
    
    def test_create_overtime_weekend(self):
        """Test creating weekend overtime (coefficient 1.5)"""
        overtime_data = {
            "employee_id": self.test_employee["id"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overtime_type": "weekend",
            "hours": 4,
            "notes": "TEST - Weekend overtime"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                json=overtime_data, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        salary = self.test_employee.get("salary", 800)
        hourly_rate = salary / 176
        expected_pay = round(4 * hourly_rate * 1.5, 2)
        
        assert abs(data["calculated_pay"] - expected_pay) < 0.1
        print(f"✓ Weekend overtime: {data['hours']}h = €{data['calculated_pay']} (x1.5)")
        
        return data["id"]
    
    def test_create_overtime_holiday(self):
        """Test creating holiday overtime (coefficient 2.0)"""
        overtime_data = {
            "employee_id": self.test_employee["id"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overtime_type": "holiday",
            "hours": 5,
            "notes": "TEST - Holiday overtime"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                json=overtime_data, headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        salary = self.test_employee.get("salary", 800)
        hourly_rate = salary / 176
        expected_pay = round(5 * hourly_rate * 2.0, 2)
        
        assert abs(data["calculated_pay"] - expected_pay) < 0.1
        print(f"✓ Holiday overtime: {data['hours']}h = €{data['calculated_pay']} (x2.0)")
        
        return data["id"]
    
    def test_list_overtime_entries(self):
        """Test listing overtime entries"""
        response = requests.get(f"{BASE_URL}/api/healthpro/overtime", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} overtime entries")
        
        if len(data) > 0:
            entry = data[0]
            assert "id" in entry
            assert "employee_id" in entry
            assert "hours" in entry
            assert "overtime_type" in entry
            assert "calculated_pay" in entry
    
    def test_list_overtime_by_employee(self):
        """Test filtering overtime by employee"""
        response = requests.get(
            f"{BASE_URL}/api/healthpro/overtime?employee_id={self.test_employee['id']}", 
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for entry in data:
            assert entry["employee_id"] == self.test_employee["id"]
        print(f"✓ Filtered overtime for employee: {len(data)} entries")
    
    def test_monthly_overtime_summary(self):
        """Test monthly overtime summary endpoint"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/healthpro/overtime/summary/{self.test_employee['id']}?month={month}&year={year}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "employee_id" in data
        assert "employee_name" in data
        assert "normal_hours" in data
        assert "night_hours" in data
        assert "weekend_hours" in data
        assert "holiday_hours" in data
        assert "total_overtime_hours" in data
        assert "total_overtime_pay" in data
        assert "base_salary" in data
        
        print(f"✓ Monthly summary for {data['employee_name']}:")
        print(f"  Normal: {data['normal_hours']}h, Night: {data['night_hours']}h")
        print(f"  Weekend: {data['weekend_hours']}h, Holiday: {data['holiday_hours']}h")
        print(f"  Total: {data['total_overtime_hours']}h = €{data['total_overtime_pay']}")
    
    def test_monthly_report(self):
        """Test monthly overtime report for all employees"""
        month = datetime.now().month
        year = datetime.now().year
        
        response = requests.get(
            f"{BASE_URL}/api/healthpro/overtime/monthly-report?month={month}&year={year}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "month" in data
        assert "year" in data
        assert "employees" in data
        assert "totals" in data
        
        print(f"✓ Monthly report for {month}/{year}:")
        print(f"  Employees: {data['totals']['total_employees']}")
        print(f"  Total hours: {data['totals']['total_overtime_hours']}")
        print(f"  Total pay: €{data['totals']['total_overtime_pay']}")
    
    def test_get_overtime_coefficients(self):
        """Test getting overtime coefficients"""
        response = requests.get(f"{BASE_URL}/api/healthpro/overtime/coefficients", 
                               headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["normal"] == 1.25
        assert data["night"] == 1.5
        assert data["weekend"] == 1.5
        assert data["holiday"] == 2.0
        print(f"✓ Overtime coefficients: normal={data['normal']}, night={data['night']}, weekend={data['weekend']}, holiday={data['holiday']}")
    
    def test_delete_overtime_entry(self):
        """Test deleting an overtime entry"""
        # First create an entry
        overtime_data = {
            "employee_id": self.test_employee["id"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "overtime_type": "normal",
            "hours": 1,
            "notes": "TEST - To be deleted"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                       json=overtime_data, headers=self.headers)
        if create_response.status_code != 200:
            pytest.skip("Could not create overtime entry for delete test")
        
        entry_id = create_response.json()["id"]
        
        # Delete the entry
        delete_response = requests.delete(f"{BASE_URL}/api/healthpro/overtime/{entry_id}", 
                                         headers=self.headers)
        assert delete_response.status_code == 200
        print(f"✓ Overtime entry deleted successfully")


class TestHealthPROVisitors:
    """Visitor user management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_visitors(self):
        """Test listing all visitors"""
        response = requests.get(f"{BASE_URL}/api/healthpro/visitors", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} visitors")
    
    def test_create_visitor(self):
        """Test creating a new visitor user"""
        unique_id = str(uuid.uuid4())[:8]
        visitor_data = {
            "full_name": "TEST_Visitor User",
            "username": f"test_visitor_{unique_id}",
            "password": "visitor123",
            "email": f"visitor_{unique_id}@test.com",
            "notes": "Test visitor - read-only access"
        }
        
        response = requests.post(f"{BASE_URL}/api/healthpro/visitors", 
                                json=visitor_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["full_name"] == "TEST_Visitor User"
        assert data["role"] == "visitor"
        assert data["is_active"] == True
        
        print(f"✓ Created visitor: {data['full_name']} (@{data['username']})")
        
        # Store for other tests
        self.created_visitor_id = data["id"]
        self.created_visitor_username = visitor_data["username"]
        self.created_visitor_password = visitor_data["password"]
        
        return data
    
    def test_visitor_login_and_limited_access(self):
        """Test that visitor can login and has limited access"""
        # First create a visitor
        unique_id = str(uuid.uuid4())[:8]
        visitor_data = {
            "full_name": "TEST_Login Visitor",
            "username": f"test_login_vis_{unique_id}",
            "password": "vis123",
            "email": f"login_vis_{unique_id}@test.com"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/healthpro/visitors", 
                                       json=visitor_data, headers=self.headers)
        if create_response.status_code != 200:
            pytest.skip("Could not create visitor for login test")
        
        visitor_id = create_response.json()["id"]
        
        # Login as visitor
        login_response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json={
            "username": visitor_data["username"],
            "password": visitor_data["password"]
        })
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        assert login_data["user"]["role"] == "visitor"
        print(f"✓ Visitor login successful - role: {login_data['user']['role']}")
        
        visitor_token = login_data["access_token"]
        visitor_headers = {"Authorization": f"Bearer {visitor_token}"}
        
        # Visitor should be able to read employees
        read_response = requests.get(f"{BASE_URL}/api/healthpro/employees", headers=visitor_headers)
        assert read_response.status_code == 200
        print(f"✓ Visitor can read employees (read-only access)")
        
        # Visitor should NOT be able to create employees
        create_emp_response = requests.post(f"{BASE_URL}/api/healthpro/employees", json={
            "first_name": "Should",
            "last_name": "Fail",
            "username": "should_fail",
            "password": "test123",
            "role": "support"
        }, headers=visitor_headers)
        assert create_emp_response.status_code == 403
        print(f"✓ Visitor correctly denied write access (403)")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}", headers=self.headers)
    
    def test_toggle_visitor_status(self):
        """Test activating/deactivating a visitor"""
        # First create a visitor
        unique_id = str(uuid.uuid4())[:8]
        visitor_data = {
            "full_name": "TEST_Toggle Visitor",
            "username": f"test_toggle_{unique_id}",
            "password": "toggle123"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/healthpro/visitors", 
                                       json=visitor_data, headers=self.headers)
        if create_response.status_code != 200:
            pytest.skip("Could not create visitor for toggle test")
        
        visitor_id = create_response.json()["id"]
        initial_status = create_response.json()["is_active"]
        assert initial_status == True
        
        # Toggle status (deactivate)
        toggle_response = requests.put(
            f"{BASE_URL}/api/healthpro/visitors/{visitor_id}/toggle-status",
            headers=self.headers
        )
        assert toggle_response.status_code == 200
        
        toggle_data = toggle_response.json()
        assert toggle_data["is_active"] == False
        print(f"✓ Visitor deactivated successfully")
        
        # Toggle again (reactivate)
        toggle_response2 = requests.put(
            f"{BASE_URL}/api/healthpro/visitors/{visitor_id}/toggle-status",
            headers=self.headers
        )
        assert toggle_response2.status_code == 200
        assert toggle_response2.json()["is_active"] == True
        print(f"✓ Visitor reactivated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}", headers=self.headers)
    
    def test_deactivated_visitor_cannot_login(self):
        """Test that deactivated visitor cannot login"""
        # Create and deactivate a visitor
        unique_id = str(uuid.uuid4())[:8]
        visitor_data = {
            "full_name": "TEST_Deactivated Visitor",
            "username": f"test_deact_{unique_id}",
            "password": "deact123"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/healthpro/visitors", 
                                       json=visitor_data, headers=self.headers)
        if create_response.status_code != 200:
            pytest.skip("Could not create visitor")
        
        visitor_id = create_response.json()["id"]
        
        # Deactivate
        requests.put(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}/toggle-status",
                    headers=self.headers)
        
        # Try to login
        login_response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json={
            "username": visitor_data["username"],
            "password": visitor_data["password"]
        })
        assert login_response.status_code == 401
        print(f"✓ Deactivated visitor correctly denied login")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}", headers=self.headers)
    
    def test_delete_visitor(self):
        """Test permanently deleting a visitor"""
        # Create a visitor
        unique_id = str(uuid.uuid4())[:8]
        visitor_data = {
            "full_name": "TEST_Delete Visitor",
            "username": f"test_del_vis_{unique_id}",
            "password": "del123"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/healthpro/visitors", 
                                       json=visitor_data, headers=self.headers)
        if create_response.status_code != 200:
            pytest.skip("Could not create visitor for delete test")
        
        visitor_id = create_response.json()["id"]
        
        # Delete the visitor
        delete_response = requests.delete(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}", 
                                         headers=self.headers)
        assert delete_response.status_code == 200
        print(f"✓ Visitor deleted successfully")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/healthpro/visitors/{visitor_id}", 
                                   headers=self.headers)
        assert get_response.status_code == 404
        print(f"✓ Verified visitor no longer exists")


class TestHealthPROOvertimeCalculation:
    """Detailed overtime calculation verification tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test employee with known salary"""
        response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create employee with €800 salary for predictable calculations
        unique_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/healthpro/employees", json={
            "first_name": "TEST_Calc",
            "last_name": "Employee",
            "username": f"test_calc_{unique_id}",
            "password": "test123",
            "role": "nurse",
            "salary": 800
        }, headers=self.headers)
        
        if create_resp.status_code == 200:
            self.test_employee = create_resp.json()
            self.employee_created = True
        else:
            # Find existing employee with salary
            emp_resp = requests.get(f"{BASE_URL}/api/healthpro/employees", headers=self.headers)
            if emp_resp.status_code == 200:
                for emp in emp_resp.json():
                    if emp.get("salary", 0) > 0:
                        self.test_employee = emp
                        self.employee_created = False
                        break
                else:
                    pytest.skip("No employee with salary found")
            else:
                pytest.skip("Could not get employees")
    
    def test_overtime_calculation_formula(self):
        """
        Verify overtime calculation formula:
        calculated_pay = hours * (base_salary / 176) * coefficient
        
        For €800 salary:
        - hourly_rate = 800 / 176 = €4.545454...
        - Normal (x1.25): 3h * 4.545 * 1.25 = €17.05
        - Night (x1.5): 2h * 4.545 * 1.5 = €13.64
        - Weekend (x1.5): 4h * 4.545 * 1.5 = €27.27
        - Holiday (x2.0): 5h * 4.545 * 2.0 = €45.45
        """
        salary = self.test_employee.get("salary", 800)
        hourly_rate = salary / 176
        
        test_cases = [
            ("normal", 3, 1.25),
            ("night", 2, 1.5),
            ("weekend", 4, 1.5),
            ("holiday", 5, 2.0)
        ]
        
        created_ids = []
        
        for overtime_type, hours, coefficient in test_cases:
            overtime_data = {
                "employee_id": self.test_employee["id"],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "overtime_type": overtime_type,
                "hours": hours,
                "notes": f"TEST - Calculation verification ({overtime_type})"
            }
            
            response = requests.post(f"{BASE_URL}/api/healthpro/overtime", 
                                    json=overtime_data, headers=self.headers)
            assert response.status_code == 200
            
            data = response.json()
            expected_pay = round(hours * hourly_rate * coefficient, 2)
            actual_pay = data["calculated_pay"]
            
            # Allow small floating point difference
            assert abs(actual_pay - expected_pay) < 0.02, \
                f"{overtime_type}: Expected €{expected_pay}, got €{actual_pay}"
            
            print(f"✓ {overtime_type.upper()}: {hours}h * €{hourly_rate:.2f} * {coefficient} = €{actual_pay}")
            created_ids.append(data["id"])
        
        # Cleanup
        for entry_id in created_ids:
            requests.delete(f"{BASE_URL}/api/healthpro/overtime/{entry_id}", headers=self.headers)
        
        print(f"\n✓ All overtime calculations verified correctly!")


# Cleanup fixture to remove TEST_ prefixed data
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup TEST_ prefixed data after all tests"""
    yield
    
    # Login as admin
    response = requests.post(f"{BASE_URL}/api/healthpro/auth/login", json=HP_ADMIN_CREDS)
    if response.status_code != 200:
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Cleanup test employees
    emp_response = requests.get(f"{BASE_URL}/api/healthpro/employees", headers=headers)
    if emp_response.status_code == 200:
        for emp in emp_response.json():
            if emp.get("first_name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/healthpro/employees/{emp['id']}", headers=headers)
    
    # Cleanup test visitors
    vis_response = requests.get(f"{BASE_URL}/api/healthpro/visitors", headers=headers)
    if vis_response.status_code == 200:
        for vis in vis_response.json():
            if vis.get("full_name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/healthpro/visitors/{vis['id']}", headers=headers)
    
    print("\n✓ Test data cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
