#!/usr/bin/env python3
"""
Test script for staff assignment locking functionality
Tests the business logic for staff assignment locking in enquiry records
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust if your server runs on different port
API_BASE = f"{BASE_URL}/api"

class StaffLockingTester:
    def __init__(self):
        self.token = None
        self.test_results = []
    
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        print()
    
    def authenticate(self):
        """Authenticate and get JWT token"""
        print("🔐 Authenticating...")
        
        # Try to authenticate (you may need to adjust credentials)
        auth_data = {
            "username": "admin",  # Adjust as needed
            "password": "admin123"  # Adjust as needed
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", json=auth_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                if self.token:
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ No token in response")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def get_headers(self):
        """Get headers with JWT token"""
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def test_staff_lock_status_endpoint(self):
        """Test the staff lock status endpoint"""
        test_name = "Staff Lock Status Endpoint"
        
        try:
            response = requests.get(f"{API_BASE}/enquiries/staff-lock-status", headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['locked', 'reason', 'unassigned_old_enquiries', 'assigned_enquiries']
                
                if all(field in data for field in required_fields):
                    self.log_test(test_name, True, "Endpoint returns correct structure", data)
                    return data
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_test(test_name, False, f"Missing fields: {missing_fields}", data)
                    return None
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return None
    
    def test_enquiries_with_lock_info(self):
        """Test that enquiries endpoint includes lock information"""
        test_name = "Enquiries with Lock Info"
        
        try:
            response = requests.get(f"{API_BASE}/enquiries?limit=5", headers=self.get_headers())
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if staff_lock_status is included
                if 'staff_lock_status' in data:
                    # Check if enquiries have lock info
                    enquiries = data.get('enquiries', [])
                    if enquiries:
                        first_enquiry = enquiries[0]
                        lock_fields = ['staff_assignment_locked', 'can_assign_staff']
                        
                        if all(field in first_enquiry for field in lock_fields):
                            self.log_test(test_name, True, "Enquiries include lock information", {
                                'staff_lock_status': data['staff_lock_status'],
                                'sample_enquiry_lock_fields': {field: first_enquiry[field] for field in lock_fields}
                            })
                            return data
                        else:
                            missing_fields = [field for field in lock_fields if field not in first_enquiry]
                            self.log_test(test_name, False, f"Enquiries missing lock fields: {missing_fields}")
                            return None
                    else:
                        self.log_test(test_name, True, "No enquiries to test, but endpoint structure is correct", data['staff_lock_status'])
                        return data
                else:
                    self.log_test(test_name, False, "staff_lock_status missing from response")
                    return None
            else:
                self.log_test(test_name, False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test(test_name, False, f"Exception: {str(e)}")
            return None
    
    def create_test_enquiry(self, staff="", days_old=0):
        """Create a test enquiry"""
        test_date = datetime.utcnow() - timedelta(days=days_old)
        
        enquiry_data = {
            "date": test_date.isoformat(),
            "wati_name": f"Test User {datetime.now().microsecond}",
            "mobile_number": f"91987654{datetime.now().microsecond % 10000:04d}",
            "business_type": "Test Business",
            "business_nature": "Testing",
            "gst": "No",
            "staff": staff,
            "comments": "Test Enquiry",
            "source": "test_script"
        }
        
        try:
            # Create via public endpoint first, then update with staff if needed
            public_data = {
                "wati_name": enquiry_data["wati_name"],
                "mobile_number": enquiry_data["mobile_number"],
                "business_type": enquiry_data["business_type"],
                "business_nature": enquiry_data["business_nature"],
                "gst": enquiry_data["gst"]
            }
            
            response = requests.post(f"{API_BASE}/enquiries/public", json=public_data)
            
            if response.status_code == 201:
                data = response.json()
                enquiry_id = data.get('enquiry_id')
                
                if enquiry_id and staff:
                    # Update with staff assignment
                    update_data = {"staff": staff}
                    update_response = requests.put(
                        f"{API_BASE}/enquiries/{enquiry_id}", 
                        json=update_data, 
                        headers=self.get_headers()
                    )
                    
                    if update_response.status_code == 200:
                        return enquiry_id, update_response.json()
                    else:
                        print(f"⚠️ Failed to update enquiry with staff: {update_response.text}")
                        return enquiry_id, None
                
                return enquiry_id, data
            else:
                print(f"⚠️ Failed to create test enquiry: {response.text}")
                return None, None
                
        except Exception as e:
            print(f"⚠️ Error creating test enquiry: {str(e)}")
            return None, None
    
    def test_staff_assignment_logic(self):
        """Test the staff assignment locking logic"""
        test_name = "Staff Assignment Logic"
        
        print("🧪 Testing staff assignment logic...")
        
        # Step 1: Check initial state
        initial_status = self.test_staff_lock_status_endpoint()
        if not initial_status:
            self.log_test(test_name, False, "Could not get initial staff lock status")
            return
        
        print(f"📊 Initial state: locked={initial_status['locked']}, old_unassigned={initial_status['unassigned_old_enquiries']}, assigned={initial_status['assigned_enquiries']}")
        
        # Step 2: Create an old enquiry without staff
        print("📝 Creating old enquiry without staff...")
        old_enquiry_id, old_enquiry_data = self.create_test_enquiry(staff="", days_old=2)
        
        if not old_enquiry_id:
            self.log_test(test_name, False, "Could not create old test enquiry")
            return
        
        # Step 3: Create a new enquiry
        print("📝 Creating new enquiry...")
        new_enquiry_id, new_enquiry_data = self.create_test_enquiry(staff="", days_old=0)
        
        if not new_enquiry_id:
            self.log_test(test_name, False, "Could not create new test enquiry")
            return
        
        # Step 4: Check if staff assignments are locked
        print("🔒 Checking if staff assignments are locked...")
        status_after_creation = self.test_staff_lock_status_endpoint()
        
        if status_after_creation and status_after_creation['locked']:
            print("✅ Staff assignments are locked as expected")
            
            # Step 5: Try to assign staff to new enquiry (should fail)
            print("🚫 Trying to assign staff to new enquiry (should fail)...")
            try:
                response = requests.put(
                    f"{API_BASE}/enquiries/{new_enquiry_id}",
                    json={"staff": "Test Staff"},
                    headers=self.get_headers()
                )
                
                if response.status_code == 400:
                    error_data = response.json()
                    if "locked" in error_data.get('error', '').lower():
                        print("✅ Staff assignment to new enquiry correctly blocked")
                    else:
                        print(f"⚠️ Unexpected error: {error_data}")
                else:
                    print(f"❌ Staff assignment to new enquiry should have failed but got: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Error testing new enquiry staff assignment: {str(e)}")
            
            # Step 6: Assign staff to old enquiry (should succeed)
            print("✅ Assigning staff to old enquiry (should succeed)...")
            try:
                response = requests.put(
                    f"{API_BASE}/enquiries/{old_enquiry_id}",
                    json={"staff": "Test Staff"},
                    headers=self.get_headers()
                )
                
                if response.status_code == 200:
                    print("✅ Staff assignment to old enquiry succeeded")
                    
                    # Step 7: Check if staff assignments are now unlocked
                    print("🔓 Checking if staff assignments are now unlocked...")
                    final_status = self.test_staff_lock_status_endpoint()
                    
                    if final_status and not final_status['locked']:
                        print("✅ Staff assignments are now unlocked")
                        
                        # Step 8: Try to assign staff to new enquiry again (should succeed now)
                        print("✅ Trying to assign staff to new enquiry again (should succeed now)...")
                        try:
                            response = requests.put(
                                f"{API_BASE}/enquiries/{new_enquiry_id}",
                                json={"staff": "Test Staff 2"},
                                headers=self.get_headers()
                            )
                            
                            if response.status_code == 200:
                                print("✅ Staff assignment to new enquiry now succeeds")
                                self.log_test(test_name, True, "Staff locking logic works correctly", {
                                    'initial_locked': initial_status['locked'],
                                    'after_old_enquiry_locked': status_after_creation['locked'],
                                    'after_staff_assignment_locked': final_status['locked']
                                })
                            else:
                                print(f"❌ Staff assignment to new enquiry still fails: {response.status_code} - {response.text}")
                                self.log_test(test_name, False, "Staff assignment to new enquiry still fails after unlocking")
                        except Exception as e:
                            print(f"⚠️ Error testing final staff assignment: {str(e)}")
                            self.log_test(test_name, False, f"Exception in final test: {str(e)}")
                    else:
                        print("❌ Staff assignments are still locked after assigning to old enquiry")
                        self.log_test(test_name, False, "Staff assignments not unlocked after old enquiry assignment")
                else:
                    print(f"❌ Staff assignment to old enquiry failed: {response.status_code} - {response.text}")
                    self.log_test(test_name, False, "Could not assign staff to old enquiry")
            except Exception as e:
                print(f"⚠️ Error assigning staff to old enquiry: {str(e)}")
                self.log_test(test_name, False, f"Exception assigning staff to old enquiry: {str(e)}")
        else:
            print("ℹ️ Staff assignments are not locked initially")
            self.log_test(test_name, True, "Staff assignments not locked (no old unassigned enquiries)", status_after_creation)
    
    def cleanup_test_enquiries(self):
        """Clean up test enquiries (optional)"""
        print("🧹 Cleanup would go here if needed...")
        # Note: You might want to implement cleanup logic here
        # For now, we'll leave test data for manual inspection
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Staff Assignment Locking Tests")
        print("=" * 50)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot run tests.")
            return False
        
        # Run tests
        self.test_staff_lock_status_endpoint()
        self.test_enquiries_with_lock_info()
        self.test_staff_assignment_logic()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n🎯 All tests completed!")
        return passed == total

def main():
    """Main function"""
    print("Staff Assignment Locking Test Suite")
    print("This script tests the staff assignment locking functionality")
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print("Please start the server first with: python app.py")
        return False
    
    # Run tests
    tester = StaffLockingTester()
    success = tester.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
