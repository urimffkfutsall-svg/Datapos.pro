"""
Multi-Tenant POS System Tests
Tests tenant isolation, data segregation, and super admin functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_CREDS = {"username": "superadmin", "password": "super@admin123"}

class TestSuperAdminLogin:
    """Test super admin authentication"""
    
    def test_super_admin_login_success(self):
        """Test super admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "super_admin"
        assert data["user"]["username"] == "superadmin"
        assert data["user"]["tenant_id"] is None  # Super admin has no tenant_id
        print(f"✓ Super admin login successful, role: {data['user']['role']}")
    
    def test_super_admin_login_wrong_password(self):
        """Test super admin login with wrong password fails"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "superadmin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestTenantCRUD:
    """Test tenant CRUD operations by super admin"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, super_admin_token):
        """Get auth headers for super admin"""
        return {"Authorization": f"Bearer {super_admin_token}"}
    
    def test_create_tenant_returns_tenant_id(self, auth_headers):
        """Test creating a new tenant returns tenant_id"""
        unique_id = str(uuid.uuid4())[:8]
        tenant_data = {
            "name": f"testfirma{unique_id}",
            "company_name": f"Test Firma {unique_id}",
            "email": f"test{unique_id}@example.com",
            "phone": "+383 44 123 456",
            "address": "Test Address",
            "admin_username": f"admin_test{unique_id}",
            "admin_password": "password123",
            "admin_full_name": "Test Admin"
        }
        
        response = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data, headers=auth_headers)
        assert response.status_code == 200, f"Create tenant failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain tenant_id"
        assert data["name"] == tenant_data["name"]
        assert data["company_name"] == tenant_data["company_name"]
        assert data["email"] == tenant_data["email"]
        assert data["status"] == "trial"  # New tenants start in trial
        print(f"✓ Tenant created with id: {data['id']}")
        
        # Cleanup - delete the tenant
        delete_response = requests.delete(f"{BASE_URL}/api/tenants/{data['id']}", headers=auth_headers)
        assert delete_response.status_code == 200
        print(f"✓ Tenant cleaned up")
    
    def test_get_all_tenants(self, auth_headers):
        """Test super admin can get all tenants"""
        response = requests.get(f"{BASE_URL}/api/tenants", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} tenants")
    
    def test_create_tenant_duplicate_name_fails(self, auth_headers):
        """Test creating tenant with duplicate name fails"""
        unique_id = str(uuid.uuid4())[:8]
        tenant_data = {
            "name": f"duptest{unique_id}",
            "company_name": "Duplicate Test",
            "email": f"dup{unique_id}@example.com",
            "admin_username": f"admin_dup{unique_id}",
            "admin_password": "password123",
            "admin_full_name": "Dup Admin"
        }
        
        # Create first tenant
        response1 = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data, headers=auth_headers)
        assert response1.status_code == 200
        tenant_id = response1.json()["id"]
        
        # Try to create duplicate
        tenant_data["email"] = f"dup2{unique_id}@example.com"  # Different email
        tenant_data["admin_username"] = f"admin_dup2{unique_id}"
        response2 = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data, headers=auth_headers)
        assert response2.status_code == 400, "Should fail with duplicate name"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tenants/{tenant_id}", headers=auth_headers)
        print("✓ Duplicate tenant name correctly rejected")


class TestTenantIsolation:
    """Test data isolation between tenants"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def setup_two_tenants(self, super_admin_token):
        """Create two tenants for isolation testing"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        unique_id1 = str(uuid.uuid4())[:8]
        unique_id2 = str(uuid.uuid4())[:8]
        
        # Create tenant 1
        tenant1_data = {
            "name": f"tenant1_{unique_id1}",
            "company_name": f"Tenant One {unique_id1}",
            "email": f"tenant1_{unique_id1}@example.com",
            "admin_username": f"admin_t1_{unique_id1}",
            "admin_password": "password123",
            "admin_full_name": "Admin One"
        }
        resp1 = requests.post(f"{BASE_URL}/api/tenants", json=tenant1_data, headers=headers)
        assert resp1.status_code == 200, f"Failed to create tenant 1: {resp1.text}"
        tenant1 = resp1.json()
        
        # Create tenant 2
        tenant2_data = {
            "name": f"tenant2_{unique_id2}",
            "company_name": f"Tenant Two {unique_id2}",
            "email": f"tenant2_{unique_id2}@example.com",
            "admin_username": f"admin_t2_{unique_id2}",
            "admin_password": "password123",
            "admin_full_name": "Admin Two"
        }
        resp2 = requests.post(f"{BASE_URL}/api/tenants", json=tenant2_data, headers=headers)
        assert resp2.status_code == 200, f"Failed to create tenant 2: {resp2.text}"
        tenant2 = resp2.json()
        
        yield {
            "tenant1": tenant1,
            "tenant1_admin": {"username": tenant1_data["admin_username"], "password": "password123"},
            "tenant2": tenant2,
            "tenant2_admin": {"username": tenant2_data["admin_username"], "password": "password123"},
            "super_admin_headers": headers
        }
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tenants/{tenant1['id']}", headers=headers)
        requests.delete(f"{BASE_URL}/api/tenants/{tenant2['id']}", headers=headers)
        print("✓ Test tenants cleaned up")
    
    def test_tenant_admin_login(self, setup_two_tenants):
        """Test tenant admin can login"""
        creds = setup_two_tenants["tenant1_admin"]
        response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        assert response.status_code == 200, f"Tenant admin login failed: {response.text}"
        
        data = response.json()
        assert data["user"]["role"] == "admin"
        assert data["user"]["tenant_id"] == setup_two_tenants["tenant1"]["id"]
        print(f"✓ Tenant admin login successful, tenant_id: {data['user']['tenant_id']}")
    
    def test_product_created_with_tenant_id(self, setup_two_tenants):
        """Test product is saved with tenant_id"""
        # Login as tenant 1 admin
        creds = setup_two_tenants["tenant1_admin"]
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a product
        product_data = {
            "name": "Test Product Tenant 1",
            "barcode": f"TEST{uuid.uuid4().hex[:8]}",
            "sale_price": 10.99,
            "purchase_price": 5.99,
            "category": "Test Category"
        }
        
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers)
        assert response.status_code == 200, f"Create product failed: {response.text}"
        
        product = response.json()
        assert "id" in product
        print(f"✓ Product created with id: {product['id']}")
        
        # Verify product is returned when querying
        get_resp = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert get_resp.status_code == 200
        products = get_resp.json()
        assert any(p["id"] == product["id"] for p in products), "Created product should be in list"
        print(f"✓ Product found in tenant's product list")
    
    def test_tenant_isolation_products(self, setup_two_tenants):
        """Test tenant 2 cannot see tenant 1's products"""
        # Login as tenant 1 admin and create product
        creds1 = setup_two_tenants["tenant1_admin"]
        login1 = requests.post(f"{BASE_URL}/api/auth/login", json=creds1)
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        product_data = {
            "name": "Isolated Product T1",
            "barcode": f"ISO{uuid.uuid4().hex[:8]}",
            "sale_price": 25.00
        }
        create_resp = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=headers1)
        assert create_resp.status_code == 200
        product_id = create_resp.json()["id"]
        print(f"✓ Product created by tenant 1: {product_id}")
        
        # Login as tenant 2 admin
        creds2 = setup_two_tenants["tenant2_admin"]
        login2 = requests.post(f"{BASE_URL}/api/auth/login", json=creds2)
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Get products as tenant 2 - should NOT see tenant 1's product
        get_resp = requests.get(f"{BASE_URL}/api/products", headers=headers2)
        assert get_resp.status_code == 200
        products = get_resp.json()
        
        # Verify tenant 1's product is NOT in tenant 2's list
        tenant1_product_ids = [p["id"] for p in products if p.get("name") == "Isolated Product T1"]
        assert len(tenant1_product_ids) == 0, "Tenant 2 should NOT see tenant 1's products"
        print(f"✓ Tenant isolation verified - Tenant 2 sees {len(products)} products (none from Tenant 1)")
    
    def test_branch_created_with_tenant_id(self, setup_two_tenants):
        """Test branch is saved with tenant_id"""
        creds = setup_two_tenants["tenant1_admin"]
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        branch_data = {
            "name": "Test Branch",
            "address": "Test Address",
            "phone": "+383 44 111 222"
        }
        
        response = requests.post(f"{BASE_URL}/api/branches", json=branch_data, headers=headers)
        assert response.status_code == 200, f"Create branch failed: {response.text}"
        
        branch = response.json()
        assert "id" in branch
        print(f"✓ Branch created with id: {branch['id']}")
        
        # Verify branch is in list
        get_resp = requests.get(f"{BASE_URL}/api/branches", headers=headers)
        assert get_resp.status_code == 200
        branches = get_resp.json()
        assert any(b["id"] == branch["id"] for b in branches)
        print(f"✓ Branch found in tenant's branch list")
    
    def test_warehouse_created_with_tenant_id(self, setup_two_tenants):
        """Test warehouse is saved with tenant_id"""
        creds = setup_two_tenants["tenant1_admin"]
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        warehouse_data = {
            "name": "Test Warehouse",
            "code": f"WH{uuid.uuid4().hex[:4]}",
            "address": "Warehouse Address"
        }
        
        response = requests.post(f"{BASE_URL}/api/warehouses", json=warehouse_data, headers=headers)
        assert response.status_code == 200, f"Create warehouse failed: {response.text}"
        
        warehouse = response.json()
        assert "id" in warehouse
        print(f"✓ Warehouse created with id: {warehouse['id']}")


class TestDashboardTenantIsolation:
    """Test dashboard returns only tenant's data"""
    
    @pytest.fixture
    def super_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def setup_tenant_with_data(self, super_admin_token):
        """Create a tenant with some data"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        # Create tenant
        tenant_data = {
            "name": f"dashtest{unique_id}",
            "company_name": f"Dashboard Test {unique_id}",
            "email": f"dash{unique_id}@example.com",
            "admin_username": f"admin_dash{unique_id}",
            "admin_password": "password123",
            "admin_full_name": "Dashboard Admin"
        }
        resp = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data, headers=headers)
        assert resp.status_code == 200
        tenant = resp.json()
        
        # Login as tenant admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": tenant_data["admin_username"],
            "password": "password123"
        })
        tenant_token = login_resp.json()["access_token"]
        tenant_headers = {"Authorization": f"Bearer {tenant_token}"}
        
        # Create some products
        for i in range(3):
            requests.post(f"{BASE_URL}/api/products", json={
                "name": f"Dashboard Product {i}",
                "sale_price": 10.00 + i
            }, headers=tenant_headers)
        
        yield {
            "tenant": tenant,
            "tenant_headers": tenant_headers,
            "super_admin_headers": headers
        }
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tenants/{tenant['id']}", headers=headers)
    
    def test_dashboard_returns_tenant_data_only(self, setup_tenant_with_data):
        """Test /api/reports/dashboard returns only tenant's data"""
        headers = setup_tenant_with_data["tenant_headers"]
        
        response = requests.get(f"{BASE_URL}/api/reports/dashboard", headers=headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        assert "total_products" in data
        assert "total_sales_today" in data
        assert "total_transactions_today" in data
        assert "low_stock_products" in data
        
        # Should have at least the 3 products we created
        assert data["total_products"] >= 3, f"Expected at least 3 products, got {data['total_products']}"
        print(f"✓ Dashboard returns tenant data: {data['total_products']} products, {data['total_transactions_today']} transactions")


class TestNonSuperAdminCannotAccessTenants:
    """Test that non-super-admin users cannot access tenant management"""
    
    @pytest.fixture
    def super_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPER_ADMIN_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def tenant_admin_token(self, super_admin_token):
        """Create a tenant and get admin token"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        unique_id = str(uuid.uuid4())[:8]
        
        tenant_data = {
            "name": f"accesstest{unique_id}",
            "company_name": f"Access Test {unique_id}",
            "email": f"access{unique_id}@example.com",
            "admin_username": f"admin_access{unique_id}",
            "admin_password": "password123",
            "admin_full_name": "Access Admin"
        }
        resp = requests.post(f"{BASE_URL}/api/tenants", json=tenant_data, headers=headers)
        tenant = resp.json()
        
        # Login as tenant admin
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": tenant_data["admin_username"],
            "password": "password123"
        })
        
        yield {
            "token": login_resp.json()["access_token"],
            "tenant_id": tenant["id"],
            "super_admin_headers": headers
        }
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tenants/{tenant['id']}", headers=headers)
    
    def test_tenant_admin_cannot_list_tenants(self, tenant_admin_token):
        """Test tenant admin cannot access /api/tenants"""
        headers = {"Authorization": f"Bearer {tenant_admin_token['token']}"}
        
        response = requests.get(f"{BASE_URL}/api/tenants", headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tenant admin correctly denied access to tenant list")
    
    def test_tenant_admin_cannot_create_tenant(self, tenant_admin_token):
        """Test tenant admin cannot create new tenants"""
        headers = {"Authorization": f"Bearer {tenant_admin_token['token']}"}
        
        response = requests.post(f"{BASE_URL}/api/tenants", json={
            "name": "unauthorized",
            "company_name": "Unauthorized",
            "email": "unauth@example.com",
            "admin_username": "unauth_admin",
            "admin_password": "password123",
            "admin_full_name": "Unauth Admin"
        }, headers=headers)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Tenant admin correctly denied creating new tenant")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
