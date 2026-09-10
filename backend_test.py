#!/usr/bin/env python3
"""
t3next POS System Backend API Test Suite
Tests all major API endpoints for the Albanian POS system
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class T3NextPOSAPITester:
    def __init__(self, base_url: str = "https://salon-pos-system-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.created_resources = {
            'products': [],
            'branches': [],
            'users': [],
            'sales': []
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")
        
        if success:
            self.tests_passed += 1
        else:
            self.failed_tests.append(f"{name}: {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> tuple:
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}
            
            return True, {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'headers': dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}
        except json.JSONDecodeError:
            return False, {"error": "Invalid JSON response"}

    def test_health_check(self):
        """Test basic API health"""
        success, result = self.make_request('GET', '/')
        if success and result['status_code'] == 200:
            self.log_test("API Health Check", True, f"API is responding: {result['data'].get('message', 'OK')}")
            return True
        else:
            self.log_test("API Health Check", False, f"API not responding: {result.get('error', 'Unknown error')}")
            return False

    def test_admin_initialization(self):
        """Test admin user creation"""
        success, result = self.make_request('POST', '/init/admin')
        if success and result['status_code'] in [200, 400]:  # 400 if admin already exists
            self.log_test("Admin Initialization", True, "Admin user ready")
            return True
        else:
            self.log_test("Admin Initialization", False, f"Failed: {result.get('error', 'Unknown error')}")
            return False

    def test_login(self):
        """Test login with admin credentials"""
        login_data = {
            "email": "admin@t3next.com",
            "password": "admin123"
        }
        
        success, result = self.make_request('POST', '/auth/login', login_data)
        if success and result['status_code'] == 200:
            data = result['data']
            if 'access_token' in data and 'user' in data:
                self.token = data['access_token']
                self.user_id = data['user']['id']
                self.log_test("Admin Login", True, f"Logged in as {data['user']['full_name']}")
                return True
        
        self.log_test("Admin Login", False, f"Login failed: {result.get('error', 'Invalid credentials')}")
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, result = self.make_request('GET', '/auth/me')
        if success and result['status_code'] == 200:
            user_data = result['data']
            self.log_test("Get Current User", True, f"User: {user_data.get('full_name', 'Unknown')}")
            return True
        else:
            self.log_test("Get Current User", False, f"Failed: {result.get('error', 'Unknown error')}")
            return False

    def test_branches_crud(self):
        """Test branch CRUD operations"""
        # Create branch
        branch_data = {
            "name": "Test Branch",
            "address": "Test Address 123",
            "phone": "+355691234567",
            "is_active": True
        }
        
        success, result = self.make_request('POST', '/branches', branch_data)
        if success and result['status_code'] == 200:
            branch_id = result['data']['id']
            self.created_resources['branches'].append(branch_id)
            self.log_test("Create Branch", True, f"Branch created: {branch_id}")
            
            # Get branches
            success, result = self.make_request('GET', '/branches')
            if success and result['status_code'] == 200:
                branches = result['data']
                self.log_test("Get Branches", True, f"Found {len(branches)} branches")
                
                # Get specific branch
                success, result = self.make_request('GET', f'/branches/{branch_id}')
                if success and result['status_code'] == 200:
                    self.log_test("Get Branch by ID", True, f"Retrieved branch: {result['data']['name']}")
                    return True
        
        self.log_test("Branches CRUD", False, "Branch operations failed")
        return False

    def test_products_crud(self):
        """Test product CRUD operations"""
        # Create product
        product_data = {
            "name": "Test Product",
            "barcode": "1234567890123",
            "purchase_price": 1.50,
            "sale_price": 2.00,
            "category": "Test Category",
            "subcategory": "Test Subcategory",
            "vat_rate": 20.0,
            "supplier": "Test Supplier",
            "unit": "copë",
            "initial_stock": 100
        }
        
        success, result = self.make_request('POST', '/products', product_data)
        if success and result['status_code'] == 200:
            product_id = result['data']['id']
            self.created_resources['products'].append(product_id)
            self.log_test("Create Product", True, f"Product created: {product_id}")
            
            # Get products
            success, result = self.make_request('GET', '/products')
            if success and result['status_code'] == 200:
                products = result['data']
                self.log_test("Get Products", True, f"Found {len(products)} products")
                
                # Get product by barcode
                success, result = self.make_request('GET', f'/products/barcode/{product_data["barcode"]}')
                if success and result['status_code'] == 200:
                    self.log_test("Get Product by Barcode", True, f"Retrieved: {result['data']['name']}")
                    
                    # Update product
                    update_data = {"name": "Updated Test Product", "sale_price": 2.50}
                    success, result = self.make_request('PUT', f'/products/{product_id}', update_data)
                    if success and result['status_code'] == 200:
                        self.log_test("Update Product", True, "Product updated successfully")
                        return True
        
        self.log_test("Products CRUD", False, "Product operations failed")
        return False

    def test_stock_management(self):
        """Test stock movement operations"""
        if not self.created_resources['products']:
            self.log_test("Stock Management", False, "No products available for stock test")
            return False
        
        product_id = self.created_resources['products'][0]
        
        # Add stock movement
        movement_data = {
            "product_id": product_id,
            "quantity": 50,
            "movement_type": "in",
            "reason": "Test stock addition",
            "reference": "TEST-001"
        }
        
        success, result = self.make_request('POST', '/stock/movements', movement_data)
        if success and result['status_code'] == 200:
            self.log_test("Create Stock Movement", True, f"Added {movement_data['quantity']} units")
            
            # Get stock movements
            success, result = self.make_request('GET', '/stock/movements', params={'product_id': product_id})
            if success and result['status_code'] == 200:
                movements = result['data']
                self.log_test("Get Stock Movements", True, f"Found {len(movements)} movements")
                return True
        
        self.log_test("Stock Management", False, "Stock operations failed")
        return False

    def test_cash_drawer_operations(self):
        """Test cash drawer operations"""
        # Open cash drawer
        drawer_data = {"opening_balance": 100.00}
        
        success, result = self.make_request('POST', '/cashier/open', drawer_data)
        if success and result['status_code'] == 200:
            drawer_id = result['data']['id']
            self.log_test("Open Cash Drawer", True, f"Drawer opened: {drawer_id}")
            
            # Get current drawer
            success, result = self.make_request('GET', '/cashier/current')
            if success and result['status_code'] == 200:
                self.log_test("Get Current Drawer", True, f"Balance: €{result['data']['current_balance']}")
                
                # Add transaction
                transaction_data = {
                    "amount": 10.00,
                    "transaction_type": "in",
                    "description": "Test transaction"
                }
                
                success, result = self.make_request('POST', '/cashier/transaction', transaction_data)
                if success and result['status_code'] == 200:
                    self.log_test("Add Drawer Transaction", True, f"New balance: €{result['data']['new_balance']}")
                    
                    # Close drawer
                    success, result = self.make_request('POST', '/cashier/close', params={'actual_balance': 110.00})
                    if success and result['status_code'] == 200:
                        self.log_test("Close Cash Drawer", True, f"Discrepancy: €{result['data']['discrepancy']}")
                        return True
        
        self.log_test("Cash Drawer Operations", False, "Drawer operations failed")
        return False

    def test_sales_operations(self):
        """Test sales creation and retrieval"""
        if not self.created_resources['products']:
            self.log_test("Sales Operations", False, "No products available for sales test")
            return False
        
        # First open a cash drawer for sales
        drawer_data = {"opening_balance": 200.00}
        success, result = self.make_request('POST', '/cashier/open', drawer_data)
        if not success or result['status_code'] != 200:
            self.log_test("Sales Operations", False, "Could not open cash drawer for sales")
            return False
        
        product_id = self.created_resources['products'][0]
        
        # Create sale
        sale_data = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "unit_price": 2.00,
                    "discount_percent": 0,
                    "vat_percent": 20
                }
            ],
            "payment_method": "cash",
            "cash_amount": 5.00,
            "customer_name": "Test Customer"
        }
        
        success, result = self.make_request('POST', '/sales', sale_data)
        if success and result['status_code'] == 200:
            sale_id = result['data']['id']
            receipt_number = result['data']['receipt_number']
            self.created_resources['sales'].append(sale_id)
            self.log_test("Create Sale", True, f"Sale created: {receipt_number}")
            
            # Get sales
            success, result = self.make_request('GET', '/sales')
            if success and result['status_code'] == 200:
                sales = result['data']
                self.log_test("Get Sales", True, f"Found {len(sales)} sales")
                
                # Get specific sale
                success, result = self.make_request('GET', f'/sales/{sale_id}')
                if success and result['status_code'] == 200:
                    self.log_test("Get Sale by ID", True, f"Retrieved sale: {result['data']['receipt_number']}")
                    return True
        
        self.log_test("Sales Operations", False, "Sales operations failed")
        return False

    def test_users_management(self):
        """Test user management operations (admin only)"""
        # Create user
        user_data = {
            "email": "test.cashier@t3next.com",
            "full_name": "Test Cashier",
            "role": "cashier",
            "password": "testpass123",
            "is_active": True
        }
        
        success, result = self.make_request('POST', '/users', user_data)
        if success and result['status_code'] == 200:
            user_id = result['data']['id']
            self.created_resources['users'].append(user_id)
            self.log_test("Create User", True, f"User created: {user_id}")
            
            # Get users
            success, result = self.make_request('GET', '/users')
            if success and result['status_code'] == 200:
                users = result['data']
                self.log_test("Get Users", True, f"Found {len(users)} users")
                
                # Get specific user
                success, result = self.make_request('GET', f'/users/{user_id}')
                if success and result['status_code'] == 200:
                    self.log_test("Get User by ID", True, f"Retrieved: {result['data']['full_name']}")
                    return True
        
        self.log_test("Users Management", False, "User operations failed")
        return False

    def test_reports_endpoints(self):
        """Test reporting endpoints"""
        # Dashboard stats
        success, result = self.make_request('GET', '/reports/dashboard')
        if success and result['status_code'] == 200:
            stats = result['data']
            self.log_test("Dashboard Stats", True, f"Sales today: €{stats.get('total_sales_today', 0)}")
            
            # Sales report
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {'start_date': yesterday, 'end_date': today}
            success, result = self.make_request('GET', '/reports/sales', params=params)
            if success and result['status_code'] == 200:
                self.log_test("Sales Report", True, f"Report generated for {yesterday} to {today}")
                
                # Stock report
                success, result = self.make_request('GET', '/reports/stock')
                if success and result['status_code'] == 200:
                    stock_report = result['data']
                    self.log_test("Stock Report", True, f"Total products: {stock_report['summary']['total_products']}")
                    return True
        
        self.log_test("Reports Endpoints", False, "Report operations failed")
        return False

    def test_categories_endpoint(self):
        """Test categories endpoint"""
        success, result = self.make_request('GET', '/categories')
        if success and result['status_code'] == 200:
            categories = result['data']
            self.log_test("Get Categories", True, f"Found {len(categories)} categories")
            return True
        else:
            self.log_test("Get Categories", False, "Categories endpoint failed")
            return False

    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n🧹 Cleaning up test resources...")
        
        # Delete created sales (if needed)
        for sale_id in self.created_resources['sales']:
            # Sales typically shouldn't be deleted, so we skip this
            pass
        
        # Delete created users
        for user_id in self.created_resources['users']:
            success, result = self.make_request('DELETE', f'/users/{user_id}')
            if success and result['status_code'] == 200:
                print(f"   Deleted user: {user_id}")
        
        # Delete created products
        for product_id in self.created_resources['products']:
            success, result = self.make_request('DELETE', f'/products/{product_id}')
            if success and result['status_code'] == 200:
                print(f"   Deleted product: {product_id}")
        
        # Delete created branches
        for branch_id in self.created_resources['branches']:
            success, result = self.make_request('DELETE', f'/branches/{branch_id}')
            if success and result['status_code'] == 200:
                print(f"   Deleted branch: {branch_id}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting t3next POS API Test Suite")
        print(f"📡 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core tests that must pass
        if not self.test_health_check():
            print("❌ API is not responding. Stopping tests.")
            return False
        
        if not self.test_admin_initialization():
            print("❌ Admin initialization failed. Stopping tests.")
            return False
        
        if not self.test_login():
            print("❌ Login failed. Stopping tests.")
            return False
        
        # Authentication tests
        self.test_get_current_user()
        
        # Core functionality tests
        self.test_branches_crud()
        self.test_products_crud()
        self.test_stock_management()
        self.test_cash_drawer_operations()
        self.test_sales_operations()
        self.test_users_management()
        self.test_reports_endpoints()
        self.test_categories_endpoint()
        
        # Cleanup
        self.cleanup_resources()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for failure in self.failed_tests:
                print(f"   • {failure}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = T3NextPOSAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())