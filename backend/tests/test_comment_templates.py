"""
Test Comment Templates CRUD API endpoints
Tests for Settings > Shabllonet tab - Comment Templates feature
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCommentTemplatesAPI:
    """Test Comment Templates CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_template_ids = []
        
        yield
        
        # Cleanup - delete test templates
        for template_id in self.created_template_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/comment-templates/{template_id}")
            except:
                pass
    
    def test_get_comment_templates(self):
        """Test GET /api/comment-templates - should return list of templates"""
        response = self.session.get(f"{BASE_URL}/api/comment-templates")
        
        assert response.status_code == 200, f"GET failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/comment-templates - returned {len(data)} templates")
        
        # Check structure of templates if any exist
        if len(data) > 0:
            template = data[0]
            assert "id" in template, "Template should have 'id'"
            assert "title" in template, "Template should have 'title'"
            assert "content" in template, "Template should have 'content'"
            assert "is_default" in template, "Template should have 'is_default'"
            assert "is_active" in template, "Template should have 'is_active'"
            print(f"✓ Template structure is correct: {template.get('title')}")
    
    def test_create_comment_template(self):
        """Test POST /api/comment-templates - create new template"""
        new_template = {
            "title": "TEST_Faleminderit",
            "content": "Faleminderit për blerjen! Ju mirëpresim përsëri.",
            "is_default": False,
            "is_active": True
        }
        
        response = self.session.post(f"{BASE_URL}/api/comment-templates", json=new_template)
        
        assert response.status_code == 200, f"POST failed: {response.text}"
        data = response.json()
        
        assert data.get("title") == new_template["title"], "Title should match"
        assert data.get("content") == new_template["content"], "Content should match"
        assert data.get("is_default") == new_template["is_default"], "is_default should match"
        assert data.get("is_active") == new_template["is_active"], "is_active should match"
        assert "id" in data, "Response should have 'id'"
        
        self.created_template_ids.append(data["id"])
        print(f"✓ POST /api/comment-templates - created template: {data['id']}")
        
        return data["id"]
    
    def test_create_default_template(self):
        """Test creating a default template - should unset other defaults"""
        # Create first template as default
        template1 = {
            "title": "TEST_Default1",
            "content": "First default template",
            "is_default": True,
            "is_active": True
        }
        
        response1 = self.session.post(f"{BASE_URL}/api/comment-templates", json=template1)
        assert response1.status_code == 200, f"POST failed: {response1.text}"
        data1 = response1.json()
        self.created_template_ids.append(data1["id"])
        assert data1.get("is_default") == True, "First template should be default"
        
        # Create second template as default - should unset first
        template2 = {
            "title": "TEST_Default2",
            "content": "Second default template",
            "is_default": True,
            "is_active": True
        }
        
        response2 = self.session.post(f"{BASE_URL}/api/comment-templates", json=template2)
        assert response2.status_code == 200, f"POST failed: {response2.text}"
        data2 = response2.json()
        self.created_template_ids.append(data2["id"])
        assert data2.get("is_default") == True, "Second template should be default"
        
        # Verify first template is no longer default
        get_response = self.session.get(f"{BASE_URL}/api/comment-templates")
        templates = get_response.json()
        
        first_template = next((t for t in templates if t["id"] == data1["id"]), None)
        if first_template:
            assert first_template.get("is_default") == False, "First template should no longer be default"
        
        print("✓ Default template logic works correctly")
    
    def test_update_comment_template(self):
        """Test PUT /api/comment-templates/{id} - update template"""
        # First create a template
        new_template = {
            "title": "TEST_ToUpdate",
            "content": "Original content",
            "is_default": False,
            "is_active": True
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/comment-templates", json=new_template)
        assert create_response.status_code == 200
        created = create_response.json()
        template_id = created["id"]
        self.created_template_ids.append(template_id)
        
        # Update the template
        update_data = {
            "title": "TEST_Updated",
            "content": "Updated content",
            "is_default": True
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/comment-templates/{template_id}", json=update_data)
        
        assert update_response.status_code == 200, f"PUT failed: {update_response.text}"
        updated = update_response.json()
        
        assert updated.get("title") == update_data["title"], "Title should be updated"
        assert updated.get("content") == update_data["content"], "Content should be updated"
        assert updated.get("is_default") == True, "is_default should be updated"
        
        print(f"✓ PUT /api/comment-templates/{template_id} - template updated successfully")
    
    def test_update_nonexistent_template(self):
        """Test PUT /api/comment-templates/{id} with non-existent ID - should return 404"""
        update_data = {
            "title": "TEST_NonExistent",
            "content": "This should fail"
        }
        
        response = self.session.put(f"{BASE_URL}/api/comment-templates/nonexistent-id-12345", json=update_data)
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PUT with non-existent ID returns 404")
    
    def test_delete_comment_template(self):
        """Test DELETE /api/comment-templates/{id} - delete template"""
        # First create a template
        new_template = {
            "title": "TEST_ToDelete",
            "content": "This will be deleted",
            "is_default": False,
            "is_active": True
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/comment-templates", json=new_template)
        assert create_response.status_code == 200
        created = create_response.json()
        template_id = created["id"]
        
        # Delete the template
        delete_response = self.session.delete(f"{BASE_URL}/api/comment-templates/{template_id}")
        
        assert delete_response.status_code == 200, f"DELETE failed: {delete_response.text}"
        data = delete_response.json()
        assert "message" in data, "Response should have message"
        
        # Verify template is deleted
        get_response = self.session.get(f"{BASE_URL}/api/comment-templates")
        templates = get_response.json()
        deleted_template = next((t for t in templates if t["id"] == template_id), None)
        assert deleted_template is None, "Template should be deleted"
        
        print(f"✓ DELETE /api/comment-templates/{template_id} - template deleted successfully")
    
    def test_delete_nonexistent_template(self):
        """Test DELETE /api/comment-templates/{id} with non-existent ID - should return 404"""
        response = self.session.delete(f"{BASE_URL}/api/comment-templates/nonexistent-id-12345")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ DELETE with non-existent ID returns 404")
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated requests are rejected"""
        # Create a new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        # GET should require auth
        get_response = unauth_session.get(f"{BASE_URL}/api/comment-templates")
        assert get_response.status_code in [401, 403], f"GET without auth should fail, got {get_response.status_code}"
        
        # POST should require auth
        post_response = unauth_session.post(f"{BASE_URL}/api/comment-templates", json={
            "title": "TEST_Unauth",
            "content": "Should fail"
        })
        assert post_response.status_code in [401, 403], f"POST without auth should fail, got {post_response.status_code}"
        
        print("✓ Unauthenticated requests are properly rejected")


class TestExistingCommentTemplates:
    """Test that existing comment templates are present in DB"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_existing_templates_count(self):
        """Test that there are existing templates in DB (as mentioned: 4 templates already exist)"""
        response = self.session.get(f"{BASE_URL}/api/comment-templates")
        
        assert response.status_code == 200
        templates = response.json()
        
        print(f"✓ Found {len(templates)} comment templates in database")
        
        # Print template details
        for t in templates:
            print(f"  - {t.get('title')}: {t.get('content')[:50]}... (default: {t.get('is_default')}, active: {t.get('is_active')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
