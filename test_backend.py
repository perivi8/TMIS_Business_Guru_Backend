#!/usr/bin/env python3
"""
Test script to verify backend is working after deployment
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://tmis-business-guru-backend.onrender.com"

def test_endpoint(url, method="GET", data=None, headers=None, description=""):
    """Test a single endpoint"""
    print(f"\n🔍 Testing: {description}")
    print(f"   URL: {url}")
    print(f"   Method: {method}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS")
            try:
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
            except:
                print(f"   Response: {response.text[:200]}...")
        else:
            print("   ❌ FAILED")
            print(f"   Error: {response.text[:200]}...")
            
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ CONNECTION ERROR: {str(e)}")
        return False

def main():
    print("🚀 TMIS Backend Test Suite")
    print("=" * 40)
    print(f"Testing backend at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = []
    
    # Test 1: Health check
    tests.append(test_endpoint(
        f"{BASE_URL}/",
        description="Health Check (Root)"
    ))
    
    # Test 2: API Health check
    tests.append(test_endpoint(
        f"{BASE_URL}/api/health",
        description="API Health Check"
    ))
    
    # Test 3: Test endpoint
    tests.append(test_endpoint(
        f"{BASE_URL}/api/test",
        description="Test Endpoint (CORS Check)"
    ))
    
    # Test 4: Login endpoint
    tests.append(test_endpoint(
        f"{BASE_URL}/api/login",
        method="POST",
        description="Test Login (Get Token)"
    ))
    
    # Get token for authenticated tests
    print("\n🔑 Getting authentication token...")
    try:
        login_response = requests.post(f"{BASE_URL}/api/login", timeout=30)
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print("   ✅ Token obtained")
            
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test 5: Clients endpoint (authenticated)
            tests.append(test_endpoint(
                f"{BASE_URL}/api/clients",
                headers=headers,
                description="Clients Endpoint (Authenticated)"
            ))
            
            # Test 6: Enquiries endpoint (authenticated)
            tests.append(test_endpoint(
                f"{BASE_URL}/api/enquiries",
                headers=headers,
                description="Enquiries Endpoint (Authenticated)"
            ))
            
        else:
            print("   ❌ Failed to get token")
            
    except Exception as e:
        print(f"   ❌ Token error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 TEST SUMMARY")
    print("=" * 40)
    
    passed = sum(tests)
    total = len(tests)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        print("\n💡 Your frontend should now work with the backend!")
        print("   Try refreshing your frontend application.")
    else:
        print("⚠️  Some tests failed. Backend may still be starting up.")
        print("   Wait 1-2 minutes and run this test again.")
    
    print(f"\n🌐 Frontend URL: https://tmis-business-guru.vercel.app")
    print(f"🔧 Backend URL: {BASE_URL}")

if __name__ == "__main__":
    main()
