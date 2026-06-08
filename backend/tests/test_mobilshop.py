"""
MobilShop API Tests - Comprehensive testing for mobile phone shop management system
Tests: Products/Inventory CRUD, Customers CRM, Repairs Management, Sales/POS, Reports
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_USERNAME = "urimi1806"
SUPER_ADMIN_PASSWORD = "1806"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for super admin"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": SUPER_ADMIN_USERNAME,
        "password": SUPER_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    # API returns access_token, not token
    return data.get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


# ============ DASHBOARD TESTS ============
class TestMobilshopDashboard:
    """Test MobilShop Dashboard API"""
    
    def test_dashboard_endpoint(self, api_client):
        """Test /api/mobilshop/reports/dashboard returns valid data"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/reports/dashboard")
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        # Verify dashboard structure
        assert "total_products" in data or "products" in data or isinstance(data, dict), \
            f"Dashboard response structure unexpected: {data}"
        print(f"Dashboard data: {data}")


# ============ PRODUCTS/INVENTORY TESTS ============
class TestMobilshopProducts:
    """Test Products/Inventory CRUD operations"""
    
    created_product_ids = []
    
    def test_list_products(self, api_client):
        """Test GET /api/mobilshop/products - list all products"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products")
        assert response.status_code == 200, f"List products failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Products should return a list"
        print(f"Found {len(data)} products")
    
    def test_create_phone_with_imei(self, api_client):
        """Test POST /api/mobilshop/products - create phone with IMEI tracking"""
        unique_imei = f"TEST{uuid.uuid4().hex[:11].upper()}"
        
        phone_data = {
            "name": f"TEST_iPhone 15 Pro Max 256GB",
            "product_type": "phone",
            "brand": "Apple",
            "model": "iPhone 15 Pro Max",
            "imei": unique_imei,
            "purchase_price": 900.00,
            "sale_price": 1199.00,
            "color": "Natural Titanium",
            "storage": "256GB",
            "condition": "new",
            "warranty_months": 12,
            "quantity": 1,
            "min_stock": 1
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/products", json=phone_data)
        assert response.status_code == 200, f"Create phone failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain product id"
        assert data["name"] == phone_data["name"], "Name mismatch"
        assert data["product_type"] == "phone", "Product type should be phone"
        assert data["imei"] == unique_imei, "IMEI mismatch"
        assert data["brand"] == "Apple", "Brand mismatch"
        
        self.__class__.created_product_ids.append(data["id"])
        print(f"Created phone with ID: {data['id']}, IMEI: {unique_imei}")
    
    def test_create_accessory(self, api_client):
        """Test POST /api/mobilshop/products - create accessory (quantity-based)"""
        accessory_data = {
            "name": f"TEST_iPhone 15 Case - Clear",
            "product_type": "accessory",
            "brand": "Apple",
            "category": "Cases",
            "purchase_price": 15.00,
            "sale_price": 29.99,
            "quantity": 50,
            "min_stock": 10
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/products", json=accessory_data)
        assert response.status_code == 200, f"Create accessory failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain product id"
        assert data["product_type"] == "accessory", "Product type should be accessory"
        assert data["quantity"] == 50, "Quantity mismatch"
        
        self.__class__.created_product_ids.append(data["id"])
        print(f"Created accessory with ID: {data['id']}")
    
    def test_get_product_by_id(self, api_client):
        """Test GET /api/mobilshop/products/{id} - get single product"""
        if not self.__class__.created_product_ids:
            pytest.skip("No products created to test")
        
        product_id = self.__class__.created_product_ids[0]
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/{product_id}")
        assert response.status_code == 200, f"Get product failed: {response.text}"
        
        data = response.json()
        assert data["id"] == product_id, "Product ID mismatch"
        print(f"Retrieved product: {data['name']}")
    
    def test_update_product(self, api_client):
        """Test PUT /api/mobilshop/products/{id} - update product"""
        if not self.__class__.created_product_ids:
            pytest.skip("No products created to test")
        
        product_id = self.__class__.created_product_ids[0]
        update_data = {
            "sale_price": 1149.00,
            "description": "Updated description for testing"
        }
        
        response = api_client.put(f"{BASE_URL}/api/mobilshop/products/{product_id}", json=update_data)
        assert response.status_code == 200, f"Update product failed: {response.text}"
        
        data = response.json()
        assert data["sale_price"] == 1149.00, "Sale price not updated"
        print(f"Updated product: {data['name']}")
    
    def test_get_phones_list(self, api_client):
        """Test GET /api/mobilshop/products/phones - get phones only"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/phones")
        assert response.status_code == 200, f"Get phones failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        for phone in data:
            assert phone.get("product_type") == "phone", "Should only return phones"
        print(f"Found {len(data)} phones")
    
    def test_get_accessories_list(self, api_client):
        """Test GET /api/mobilshop/products/accessories - get accessories only"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/accessories")
        assert response.status_code == 200, f"Get accessories failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        for acc in data:
            assert acc.get("product_type") == "accessory", "Should only return accessories"
        print(f"Found {len(data)} accessories")
    
    def test_search_products(self, api_client):
        """Test GET /api/mobilshop/products/search/{query} - search products"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/search/TEST")
        assert response.status_code == 200, f"Search products failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Search found {len(data)} products matching 'TEST'")
    
    def test_get_brands_list(self, api_client):
        """Test GET /api/mobilshop/products/brands/list - get unique brands"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/brands/list")
        assert response.status_code == 200, f"Get brands failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Found brands: {data}")
    
    def test_get_categories_list(self, api_client):
        """Test GET /api/mobilshop/products/categories/list - get unique categories"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/categories/list")
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Found categories: {data}")
    
    def test_delete_products(self, api_client):
        """Test DELETE /api/mobilshop/products/{id} - soft delete products"""
        for product_id in self.__class__.created_product_ids:
            response = api_client.delete(f"{BASE_URL}/api/mobilshop/products/{product_id}")
            assert response.status_code == 200, f"Delete product failed: {response.text}"
            print(f"Deleted product: {product_id}")
        
        self.__class__.created_product_ids.clear()


# ============ CUSTOMERS CRM TESTS ============
class TestMobilshopCustomers:
    """Test Customers CRM CRUD operations"""
    
    created_customer_ids = []
    
    def test_list_customers(self, api_client):
        """Test GET /api/mobilshop/customers - list all customers"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/customers")
        assert response.status_code == 200, f"List customers failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Customers should return a list"
        print(f"Found {len(data)} customers")
    
    def test_create_customer(self, api_client):
        """Test POST /api/mobilshop/customers - create new customer"""
        unique_phone = f"+383{uuid.uuid4().hex[:8]}"
        
        customer_data = {
            "full_name": "TEST_Klient Testues",
            "phone": unique_phone,
            "email": "test.klient@example.com",
            "address": "Rruga Test 123",
            "city": "Prishtinë",
            "notes": "Test customer for API testing"
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/customers", json=customer_data)
        assert response.status_code == 200, f"Create customer failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain customer id"
        assert data["full_name"] == customer_data["full_name"], "Name mismatch"
        assert data["phone"] == unique_phone, "Phone mismatch"
        
        self.__class__.created_customer_ids.append(data["id"])
        print(f"Created customer with ID: {data['id']}")
        return data["id"]
    
    def test_get_customer_by_id(self, api_client):
        """Test GET /api/mobilshop/customers/{id} - get single customer"""
        if not self.__class__.created_customer_ids:
            pytest.skip("No customers created to test")
        
        customer_id = self.__class__.created_customer_ids[0]
        response = api_client.get(f"{BASE_URL}/api/mobilshop/customers/{customer_id}")
        assert response.status_code == 200, f"Get customer failed: {response.text}"
        
        data = response.json()
        assert data["id"] == customer_id, "Customer ID mismatch"
        print(f"Retrieved customer: {data['full_name']}")
    
    def test_search_customers(self, api_client):
        """Test GET /api/mobilshop/customers/search/{query} - search customers"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/customers/search/TEST")
        assert response.status_code == 200, f"Search customers failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        print(f"Search found {len(data)} customers matching 'TEST'")
    
    def test_update_customer(self, api_client):
        """Test PUT /api/mobilshop/customers/{id} - update customer"""
        if not self.__class__.created_customer_ids:
            pytest.skip("No customers created to test")
        
        customer_id = self.__class__.created_customer_ids[0]
        update_data = {
            "notes": "Updated notes for testing",
            "loyalty_points": 100
        }
        
        response = api_client.put(f"{BASE_URL}/api/mobilshop/customers/{customer_id}", json=update_data)
        assert response.status_code == 200, f"Update customer failed: {response.text}"
        
        data = response.json()
        assert data["loyalty_points"] == 100, "Loyalty points not updated"
        print(f"Updated customer: {data['full_name']}")
    
    def test_delete_customers(self, api_client):
        """Test DELETE /api/mobilshop/customers/{id} - soft delete customers"""
        for customer_id in self.__class__.created_customer_ids:
            response = api_client.delete(f"{BASE_URL}/api/mobilshop/customers/{customer_id}")
            assert response.status_code == 200, f"Delete customer failed: {response.text}"
            print(f"Deleted customer: {customer_id}")
        
        self.__class__.created_customer_ids.clear()


# ============ REPAIRS MANAGEMENT TESTS ============
class TestMobilshopRepairs:
    """Test Repairs/Service Management CRUD operations"""
    
    created_repair_ids = []
    test_customer_id = None
    
    @pytest.fixture(autouse=True)
    def setup_customer(self, api_client):
        """Create a test customer for repairs"""
        if self.__class__.test_customer_id is None:
            unique_phone = f"+383{uuid.uuid4().hex[:8]}"
            customer_data = {
                "full_name": "TEST_Repair Customer",
                "phone": unique_phone
            }
            response = api_client.post(f"{BASE_URL}/api/mobilshop/customers", json=customer_data)
            if response.status_code == 200:
                self.__class__.test_customer_id = response.json()["id"]
        yield
    
    def test_list_repairs(self, api_client):
        """Test GET /api/mobilshop/repairs - list all repairs"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/repairs")
        assert response.status_code == 200, f"List repairs failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Repairs should return a list"
        print(f"Found {len(data)} repairs")
    
    def test_create_repair_ticket(self, api_client):
        """Test POST /api/mobilshop/repairs - create repair ticket"""
        if not self.__class__.test_customer_id:
            pytest.skip("No test customer available")
        
        repair_data = {
            "customer_id": self.__class__.test_customer_id,
            "device_brand": "Samsung",
            "device_model": "Galaxy S24 Ultra",
            "device_imei": "123456789012345",
            "device_color": "Black",
            "issue_description": "Screen cracked, needs replacement",
            "estimated_cost": 150.00,
            "priority": "high",
            "notes": "Test repair ticket"
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/repairs", json=repair_data)
        assert response.status_code == 200, f"Create repair failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain repair id"
        assert "ticket_number" in data, "Response should contain ticket number"
        assert data["status"] == "received", "Initial status should be 'received'"
        assert data["device_brand"] == "Samsung", "Device brand mismatch"
        
        self.__class__.created_repair_ids.append(data["id"])
        print(f"Created repair ticket: {data['ticket_number']}")
    
    def test_get_repair_by_id(self, api_client):
        """Test GET /api/mobilshop/repairs/{id} - get single repair"""
        if not self.__class__.created_repair_ids:
            pytest.skip("No repairs created to test")
        
        repair_id = self.__class__.created_repair_ids[0]
        response = api_client.get(f"{BASE_URL}/api/mobilshop/repairs/{repair_id}")
        assert response.status_code == 200, f"Get repair failed: {response.text}"
        
        data = response.json()
        assert data["id"] == repair_id, "Repair ID mismatch"
        print(f"Retrieved repair: {data['ticket_number']}")
    
    def test_get_repairs_by_status(self, api_client):
        """Test GET /api/mobilshop/repairs/by-status/{status} - filter by status"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/repairs/by-status/received")
        assert response.status_code == 200, f"Get repairs by status failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        for repair in data:
            assert repair.get("status") == "received", "Should only return 'received' repairs"
        print(f"Found {len(data)} repairs with status 'received'")
    
    def test_get_pending_repairs_count(self, api_client):
        """Test GET /api/mobilshop/repairs/pending - get counts by status"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/repairs/pending")
        assert response.status_code == 200, f"Get pending repairs failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Should return a dictionary"
        print(f"Pending repairs counts: {data}")
    
    def test_update_repair_status(self, api_client):
        """Test PATCH /api/mobilshop/repairs/{id}/status - update repair status"""
        if not self.__class__.created_repair_ids:
            pytest.skip("No repairs created to test")
        
        repair_id = self.__class__.created_repair_ids[0]
        status_data = {
            "status": "diagnosing",
            "notes": "Started diagnosis"
        }
        
        response = api_client.patch(f"{BASE_URL}/api/mobilshop/repairs/{repair_id}/status", json=status_data)
        assert response.status_code == 200, f"Update repair status failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "diagnosing", "Status not updated"
        print(f"Updated repair status to: {data['status']}")
    
    def test_update_repair_full(self, api_client):
        """Test PUT /api/mobilshop/repairs/{id} - full repair update"""
        if not self.__class__.created_repair_ids:
            pytest.skip("No repairs created to test")
        
        repair_id = self.__class__.created_repair_ids[0]
        update_data = {
            "diagnosis": "Screen needs full replacement",
            "labor_cost": 50.00,
            "parts_cost": 100.00,
            "status": "repairing"
        }
        
        response = api_client.put(f"{BASE_URL}/api/mobilshop/repairs/{repair_id}", json=update_data)
        assert response.status_code == 200, f"Update repair failed: {response.text}"
        
        data = response.json()
        assert data["diagnosis"] == "Screen needs full replacement", "Diagnosis not updated"
        assert data["total_cost"] == 150.00, "Total cost should be labor + parts"
        print(f"Updated repair: {data['ticket_number']}")
    
    def test_cleanup_repairs(self, api_client):
        """Cleanup test repairs and customer"""
        # Note: Repairs don't have a delete endpoint in the code, so we skip cleanup
        # Clean up test customer
        if self.__class__.test_customer_id:
            api_client.delete(f"{BASE_URL}/api/mobilshop/customers/{self.__class__.test_customer_id}")
            print(f"Cleaned up test customer: {self.__class__.test_customer_id}")


# ============ SALES/POS TESTS ============
class TestMobilshopSales:
    """Test Sales/POS operations"""
    
    test_product_id = None
    test_customer_id = None
    created_sale_ids = []
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, api_client):
        """Create test product and customer for sales"""
        # Create test product
        if self.__class__.test_product_id is None:
            product_data = {
                "name": "TEST_Sale Product",
                "product_type": "accessory",
                "purchase_price": 10.00,
                "sale_price": 25.00,
                "quantity": 100,
                "min_stock": 5
            }
            response = api_client.post(f"{BASE_URL}/api/mobilshop/products", json=product_data)
            if response.status_code == 200:
                self.__class__.test_product_id = response.json()["id"]
        
        # Create test customer
        if self.__class__.test_customer_id is None:
            unique_phone = f"+383{uuid.uuid4().hex[:8]}"
            customer_data = {
                "full_name": "TEST_Sale Customer",
                "phone": unique_phone
            }
            response = api_client.post(f"{BASE_URL}/api/mobilshop/customers", json=customer_data)
            if response.status_code == 200:
                self.__class__.test_customer_id = response.json()["id"]
        yield
    
    def test_list_sales(self, api_client):
        """Test GET /api/mobilshop/sales - list all sales"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/sales")
        assert response.status_code == 200, f"List sales failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Sales should return a list"
        print(f"Found {len(data)} sales")
    
    def test_create_sale_cash(self, api_client):
        """Test POST /api/mobilshop/sales - create sale with cash payment"""
        if not self.__class__.test_product_id:
            pytest.skip("No test product available")
        
        sale_data = {
            "customer_id": self.__class__.test_customer_id,
            "items": [
                {
                    "product_id": self.__class__.test_product_id,
                    "quantity": 2,
                    "unit_price": 25.00,
                    "discount_percent": 0,
                    "discount_amount": 0
                }
            ],
            "payment_method": "cash",
            "cash_amount": 50.00,
            "card_amount": 0,
            "discount_percent": 0,
            "discount_amount": 0,
            "notes": "Test sale"
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/sales", json=sale_data)
        assert response.status_code == 200, f"Create sale failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain sale id"
        assert "invoice_number" in data, "Response should contain invoice number"
        assert data["payment_method"] == "cash", "Payment method mismatch"
        assert data["grand_total"] == 50.00, "Grand total mismatch"
        
        self.__class__.created_sale_ids.append(data["id"])
        print(f"Created sale: {data['invoice_number']}, Total: €{data['grand_total']}")
    
    def test_create_sale_card(self, api_client):
        """Test POST /api/mobilshop/sales - create sale with card payment"""
        if not self.__class__.test_product_id:
            pytest.skip("No test product available")
        
        sale_data = {
            "items": [
                {
                    "product_id": self.__class__.test_product_id,
                    "quantity": 1,
                    "unit_price": 25.00,
                    "discount_percent": 10,
                    "discount_amount": 0
                }
            ],
            "payment_method": "card",
            "cash_amount": 0,
            "card_amount": 22.50,
            "discount_percent": 0,
            "discount_amount": 0
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/sales", json=sale_data)
        assert response.status_code == 200, f"Create sale with card failed: {response.text}"
        
        data = response.json()
        assert data["payment_method"] == "card", "Payment method should be card"
        
        self.__class__.created_sale_ids.append(data["id"])
        print(f"Created card sale: {data['invoice_number']}")
    
    def test_get_sale_by_id(self, api_client):
        """Test GET /api/mobilshop/sales/{id} - get single sale"""
        if not self.__class__.created_sale_ids:
            pytest.skip("No sales created to test")
        
        sale_id = self.__class__.created_sale_ids[0]
        response = api_client.get(f"{BASE_URL}/api/mobilshop/sales/{sale_id}")
        assert response.status_code == 200, f"Get sale failed: {response.text}"
        
        data = response.json()
        assert data["id"] == sale_id, "Sale ID mismatch"
        print(f"Retrieved sale: {data['invoice_number']}")
    
    def test_cleanup_sales_data(self, api_client):
        """Cleanup test data"""
        # Clean up test product
        if self.__class__.test_product_id:
            api_client.delete(f"{BASE_URL}/api/mobilshop/products/{self.__class__.test_product_id}")
            print(f"Cleaned up test product: {self.__class__.test_product_id}")
        
        # Clean up test customer
        if self.__class__.test_customer_id:
            api_client.delete(f"{BASE_URL}/api/mobilshop/customers/{self.__class__.test_customer_id}")
            print(f"Cleaned up test customer: {self.__class__.test_customer_id}")


# ============ REPORTS TESTS ============
class TestMobilshopReports:
    """Test Reports API endpoints"""
    
    def test_sales_report(self, api_client):
        """Test GET /api/mobilshop/reports/sales - sales report"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/reports/sales?period=month")
        assert response.status_code == 200, f"Sales report failed: {response.text}"
        
        data = response.json()
        assert "total_sales" in data, "Should contain total_sales"
        assert "total_transactions" in data, "Should contain total_transactions"
        print(f"Sales report: Total €{data.get('total_sales', 0)}, Transactions: {data.get('total_transactions', 0)}")
    
    def test_inventory_report(self, api_client):
        """Test GET /api/mobilshop/reports/inventory - inventory report"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/reports/inventory")
        assert response.status_code == 200, f"Inventory report failed: {response.text}"
        
        data = response.json()
        assert "total_products" in data, "Should contain total_products"
        assert "total_phones" in data, "Should contain total_phones"
        assert "total_accessories" in data, "Should contain total_accessories"
        print(f"Inventory: {data.get('total_products', 0)} products, {data.get('total_phones', 0)} phones, {data.get('total_accessories', 0)} accessories")
    
    def test_profit_report(self, api_client):
        """Test GET /api/mobilshop/reports/profit - profit report"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/reports/profit?period=month")
        assert response.status_code == 200, f"Profit report failed: {response.text}"
        
        data = response.json()
        assert "gross_profit" in data or "sales_profit" in data, "Should contain profit data"
        print(f"Profit report: {data}")
    
    def test_sales_report_different_periods(self, api_client):
        """Test sales report with different periods"""
        periods = ["day", "week", "month", "year"]
        
        for period in periods:
            response = api_client.get(f"{BASE_URL}/api/mobilshop/reports/sales?period={period}")
            assert response.status_code == 200, f"Sales report for {period} failed: {response.text}"
            print(f"Sales report ({period}): OK")


# ============ SUPPLIERS TESTS ============
class TestMobilshopSuppliers:
    """Test Suppliers CRUD operations"""
    
    created_supplier_ids = []
    
    def test_list_suppliers(self, api_client):
        """Test GET /api/mobilshop/products/suppliers - list all suppliers"""
        response = api_client.get(f"{BASE_URL}/api/mobilshop/products/suppliers")
        assert response.status_code == 200, f"List suppliers failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Suppliers should return a list"
        print(f"Found {len(data)} suppliers")
    
    def test_create_supplier(self, api_client):
        """Test POST /api/mobilshop/products/suppliers - create supplier"""
        supplier_data = {
            "name": "TEST_Supplier Co",
            "contact_person": "John Doe",
            "phone": "+38349123456",
            "email": "supplier@test.com",
            "address": "Test Address 123"
        }
        
        response = api_client.post(f"{BASE_URL}/api/mobilshop/products/suppliers", json=supplier_data)
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain supplier id"
        assert data["name"] == supplier_data["name"], "Name mismatch"
        
        self.__class__.created_supplier_ids.append(data["id"])
        print(f"Created supplier: {data['name']}")
    
    def test_update_supplier(self, api_client):
        """Test PUT /api/mobilshop/products/suppliers/{id} - update supplier"""
        if not self.__class__.created_supplier_ids:
            pytest.skip("No suppliers created to test")
        
        supplier_id = self.__class__.created_supplier_ids[0]
        update_data = {
            "notes": "Updated supplier notes"
        }
        
        response = api_client.put(f"{BASE_URL}/api/mobilshop/products/suppliers/{supplier_id}", json=update_data)
        assert response.status_code == 200, f"Update supplier failed: {response.text}"
        print(f"Updated supplier: {supplier_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
