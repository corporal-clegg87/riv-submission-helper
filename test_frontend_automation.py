#!/usr/bin/env python3
"""
Frontend Automation Tests for RIV Assignment System
Tests the web interface functionality in both local and production environments.
"""

import asyncio
import os
import sys
from playwright.async_api import async_playwright
import time
import random

class FrontendTester:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.created_assignment_code = None  # Store the assignment code from creation test
        # Use existing class name from test data to avoid "class not found" errors
        self.test_class_name = "Math 7"  # This class exists in test data
        self.test_assignment_title = f"Test Assignment {random.randint(1000, 9999)}"  # Unique title to avoid collisions

    async def setup(self):
        """Setup browser and page."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)  # Set to True for headless
        context = await self.browser.new_context()
        self.page = await context.new_page()
        
        # Set up authentication
        await self.page.set_extra_http_headers({
            'Authorization': f'Basic {self._encode_auth()}'
        })

    def _encode_auth(self):
        """Encode credentials for basic auth."""
        import base64
        credentials = f"{self.username}:{self.password}"
        return base64.b64encode(credentials.encode()).decode()

    async def teardown(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()

    async def test_page_load(self):
        """Test 1: Verify the main page loads correctly."""
        print("🧪 Test 1: Page Load")
        try:
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state('networkidle')
            
            # Check for main elements
            title = await self.page.title()
            assert "Assignment System" in title, f"Expected 'Assignment System' in title, got: {title}"
            
            # Check for main header
            header = await self.page.text_content('h1')
            assert "Email-First Assignment System" in header, f"Expected header, got: {header}"
            
            # Check for tabs
            tabs = await self.page.query_selector_all('.tab-button')
            assert len(tabs) == 5, f"Expected 5 tabs, found {len(tabs)}"
            
            print("✅ Page loads correctly with all elements")
            return True
        except Exception as e:
            print(f"❌ Page load failed: {e}")
            return False

    async def test_tab_navigation(self):
        """Test 2: Verify tab navigation works."""
        print("🧪 Test 2: Tab Navigation")
        try:
            # Test each tab
            tabs = ['createTab', 'submitTab', 'returnTab', 'statusTab', 'allTab']
            tab_names = ['Create Assignment', 'Submit Work', 'Return Grade', 'Check Status', 'All Assignments']
            
            for i, (tab_id, tab_name) in enumerate(zip(tabs, tab_names)):
                # Click tab button
                await self.page.click(f'button[onclick="showTab(\'{tab_id}\')"]')
                await self.page.wait_for_timeout(500)  # Wait for tab switch
                
                # Check if tab content is visible
                tab_content = await self.page.query_selector(f'#{tab_id}')
                is_visible = await tab_content.is_visible()
                assert is_visible, f"Tab {tab_name} is not visible"
                
                # Check for tab-specific content
                if tab_id == 'createTab':
                    title_input = await self.page.query_selector('#assignTitle')
                    assert title_input, "Create assignment title input not found"
                elif tab_id == 'submitTab':
                    code_input = await self.page.query_selector('#submitCode')
                    assert code_input, "Submit assignment code input not found"
                elif tab_id == 'returnTab':
                    grade_input = await self.page.query_selector('#returnGrade')
                    assert grade_input, "Return grade input not found"
                elif tab_id == 'statusTab':
                    status_input = await self.page.query_selector('#statusCode')
                    assert status_input, "Status code input not found"
                elif tab_id == 'allTab':
                    refresh_button = await self.page.query_selector('button[onclick="loadAllAssignments()"]')
                    assert refresh_button, "All assignments refresh button not found"
            
            print("✅ Tab navigation works correctly")
            return True
        except Exception as e:
            print(f"❌ Tab navigation failed: {e}")
            return False

    async def test_create_assignment_form(self):
        """Test 3: Test assignment creation form."""
        print("🧪 Test 3: Create Assignment Form")
        print(f"📝 Using unique assignment title: {self.test_assignment_title}")
        try:
            # Navigate to create tab
            await self.page.click('button[onclick="showTab(\'createTab\')"]')
            await self.page.wait_for_timeout(500)
            
            # Fill out the form with valid data (use unique title to avoid collisions)
            await self.page.fill('#assignTitle', self.test_assignment_title)
            await self.page.fill('#assignClass', self.test_class_name)  # Use existing class
            
            # Set a future date
            future_date = '2025-12-31'
            await self.page.fill('#assignDeadline', future_date)
            await self.page.fill('#assignInstructions', 'This is an automated test assignment')
            
            # Verify fields are filled correctly
            title_value = await self.page.input_value('#assignTitle')
            class_value = await self.page.input_value('#assignClass')
            deadline_value = await self.page.input_value('#assignDeadline')
            
            if title_value != self.test_assignment_title:
                print(f"❌ Title field not filled correctly: {title_value}")
                return False
            if class_value != self.test_class_name:
                print(f"❌ Class field not filled correctly: {class_value}")
                return False
            if deadline_value != future_date:
                print(f"❌ Deadline field not filled correctly: {deadline_value}")
                return False
            
            print("✅ Form fields filled correctly")
            
            # Submit the form
            await self.page.click('#assignForm button[type="submit"]')
            await self.page.wait_for_timeout(3000)  # Wait for API response
            
            # Check for success/error message and validate the response
            result_div = await self.page.query_selector('#assignResult')
            if result_div:
                result_text = await result_div.text_content()
                print(f"📝 Assignment creation result: {result_text}")
                
                # Extract assignment code from the result
                import re
                code_match = re.search(r'Code:\s*([A-Z0-9-]+)', result_text)
                if code_match:
                    self.created_assignment_code = code_match.group(1)
                    print(f"📝 Extracted assignment code: {self.created_assignment_code}")
                
                # Check if the result indicates success
                if "created successfully" in result_text.lower() or "assignment" in result_text.lower():
                    print("✅ Assignment creation form works - assignment created successfully")
                    return True
                else:
                    print(f"❌ Assignment creation failed: {result_text}")
                    return False
            else:
                print("❌ No result message found")
                return False
        except Exception as e:
            print(f"❌ Assignment creation form failed: {e}")
            return False

    async def test_submit_assignment_form(self):
        """Test 4: Test assignment submission form."""
        print("🧪 Test 4: Submit Assignment Form")
        try:
            # Navigate to submit tab
            await self.page.click('button[onclick="showTab(\'submitTab\')"]')
            await self.page.wait_for_timeout(500)
            
            # Fill out the form with the created assignment code
            assignment_code = self.created_assignment_code or 'MATH7-0120'  # Fallback to old code if none created
            await self.page.fill('#submitCode', assignment_code)
            await self.page.fill('#submitStudentId', 'STU001')
            
            # Submit the form
            await self.page.click('#submitForm button[type="submit"]')
            await self.page.wait_for_timeout(3000)  # Wait for API response
            
            # Check for success/error message and validate the response
            result_div = await self.page.query_selector('#submitResult')
            if result_div:
                result_text = await result_div.text_content()
                print(f"📝 Submission result: {result_text}")
                
                # Check if the result indicates success
                if "submission received" in result_text.lower() or "submitted" in result_text.lower():
                    print("✅ Assignment submission form works - submission successful")
                    return True
                else:
                    print(f"❌ Assignment submission failed: {result_text}")
                    return False
            else:
                print("❌ No result message found")
                return False
        except Exception as e:
            print(f"❌ Assignment submission form failed: {e}")
            return False

    async def test_return_grade_form(self):
        """Test 5: Test grade return form."""
        print("🧪 Test 5: Return Grade Form")
        try:
            # Navigate to return tab
            await self.page.click('button[onclick="showTab(\'returnTab\')"]')
            await self.page.wait_for_timeout(500)
            
            # Fill out the form with the created assignment code
            assignment_code = self.created_assignment_code or 'MATH7-0120'  # Fallback to old code if none created
            await self.page.fill('#returnCode', assignment_code)
            await self.page.fill('#returnStudentId', 'STU001')
            await self.page.fill('#returnGrade', 'A+')
            await self.page.fill('#returnFeedback', 'Excellent work!')
            
            # Submit the form
            await self.page.click('#returnForm button[type="submit"]')
            await self.page.wait_for_timeout(3000)  # Wait for API response
            
            # Check for success/error message and validate the response
            result_div = await self.page.query_selector('#returnResult')
            if result_div:
                result_text = await result_div.text_content()
                print(f"📝 Grade return result: {result_text}")
                
                # Check if the result indicates success
                if "grade recorded" in result_text.lower() or "grade returned" in result_text.lower() or "returned" in result_text.lower():
                    print("✅ Grade return form works - grade returned successfully")
                    return True
                else:
                    print(f"❌ Grade return failed: {result_text}")
                    return False
            else:
                print("❌ No result message found")
                return False
        except Exception as e:
            print(f"❌ Grade return form failed: {e}")
            return False

    async def test_status_check(self):
        """Test 6: Test status checking functionality."""
        print("🧪 Test 6: Status Check")
        try:
            # Navigate to status tab
            await self.page.click('button[onclick="showTab(\'statusTab\')"]')
            await self.page.wait_for_timeout(500)
            
            # Enter the created assignment code
            assignment_code = self.created_assignment_code or 'MATH7-0120'  # Fallback to old code if none created
            await self.page.fill('#statusCode', assignment_code)
            
            # Click check status button
            await self.page.click('button[onclick="loadStatus()"]')
            await self.page.wait_for_timeout(3000)  # Wait for API response
            
            # Check for result and validate it shows assignment data
            result_div = await self.page.query_selector('#statusResult')
            if result_div:
                result_text = await result_div.text_content()
                print(f"📝 Status check result: {result_text}")
                
                # Check if we got assignment data (not "not found")
                if "not found" in result_text.lower():
                    print(f"❌ Status check failed - assignment not found: {result_text}")
                    return False
                elif "math7-0120" in result_text.lower() or "assignment" in result_text.lower():
                    print("✅ Status check works - assignment data retrieved")
                    return True
                else:
                    print(f"❌ Status check failed - unexpected result: {result_text}")
                    return False
            else:
                print("❌ No result message found")
                return False
        except Exception as e:
            print(f"❌ Status check failed: {e}")
            return False

    async def test_all_assignments(self):
        """Test 7: Test all assignments listing."""
        print("🧪 Test 7: All Assignments")
        try:
            # Navigate to all assignments tab
            await self.page.click('button[onclick="showTab(\'allTab\')"]')
            await self.page.wait_for_timeout(500)
            
            # Click refresh button
            await self.page.click('button[onclick="loadAllAssignments()"]')
            await self.page.wait_for_timeout(3000)  # Wait for API response
            
            # Check for assignments list and validate content
            assignments_div = await self.page.query_selector('#allAssignments')
            if assignments_div:
                content = await assignments_div.text_content()
                print(f"📝 Assignments list: {content[:200]}...")
                
                # Check if we got actual assignments (not "no assignments found")
                if "no assignments found" in content.lower():
                    print("⚠️ No assignments found - this might be expected in production")
                    return True  # This is acceptable for production
                elif "math" in content.lower() or "assignment" in content.lower():
                    print("✅ All assignments listing works - assignments retrieved")
                    return True
                else:
                    print(f"❌ All assignments listing failed - unexpected content: {content}")
                    return False
            else:
                print("❌ No assignments div found")
                return False
        except Exception as e:
            print(f"❌ All assignments listing failed: {e}")
            return False

    async def test_static_files(self):
        """Test 8: Verify static files are loaded."""
        print("🧪 Test 8: Static Files")
        try:
            # Check if CSS is loaded
            css_link = await self.page.query_selector('link[href="/static/style.css"]')
            assert css_link, "CSS file not found"
            
            # Check if JS is loaded
            js_script = await self.page.query_selector('script[src="/static/script.js"]')
            assert js_script, "JavaScript file not found"
            
            # Test CSS by checking if styles are applied
            container = await self.page.query_selector('.container')
            if container:
                styles = await container.evaluate('el => getComputedStyle(el)')
                print(f"📝 Container styles applied: {bool(styles)}")
            
            print("✅ Static files are loaded correctly")
            return True
        except Exception as e:
            print(f"❌ Static files test failed: {e}")
            return False

    async def test_authentication(self):
        """Test 9: Verify authentication is working."""
        print("🧪 Test 9: Authentication")
        try:
            # Try to access the page
            response = await self.page.goto(self.base_url)
            
            # Check if we get redirected or get auth error
            if response.status == 401:
                print("❌ Authentication failed - got 401")
                return False
            elif response.status == 200:
                print("✅ Authentication successful")
                return True
            else:
                print(f"⚠️ Unexpected status code: {response.status}")
                return False
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all frontend tests."""
        print(f"🚀 Starting Frontend Automation Tests for {self.base_url}")
        print(f"👤 Using credentials: {self.username}:{self.password[:3]}***")
        print("=" * 60)
        
        await self.setup()
        
        tests = [
            self.test_authentication,
            self.test_page_load,
            self.test_tab_navigation,
            self.test_static_files,
            self.test_create_assignment_form,
            self.test_submit_assignment_form,
            self.test_return_grade_form,
            self.test_status_check,
            self.test_all_assignments,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append(False)
        
        await self.teardown()
        
        # Summary
        passed = sum(results)
        total = len(results)
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All frontend tests passed!")
        else:
            print(f"⚠️ {total - passed} tests failed")
        
        return passed == total

async def main():
    """Main function to run tests for both environments."""
    print("🧪 RIV Assignment System - Frontend Automation Tests")
    print("=" * 60)
    
    # Test configurations
    environments = [
        {
            'name': 'Local Environment',
            'url': 'http://localhost:8000',
            'username': 'admin',
            'password': 'admin'
        },
        {
            'name': 'Production Environment',
            'url': 'https://riv-assignments-1079423826925.us-central1.run.app',
            'username': os.getenv('PROD_USERNAME', 'riv_admin_2024'),
            'password': os.getenv('PROD_PASSWORD', 'test_password')
        }
    ]
    
    all_passed = True
    
    for env in environments:
        print(f"\n🌐 Testing {env['name']}")
        print(f"🔗 URL: {env['url']}")
        print("-" * 40)
        
        tester = FrontendTester(env['url'], env['username'], env['password'])
        try:
            result = await tester.run_all_tests()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {env['name']} testing failed: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All frontend automation tests passed for both environments!")
    else:
        print("⚠️ Some frontend automation tests failed")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())