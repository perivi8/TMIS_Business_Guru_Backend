#!/usr/bin/env python3
"""
Test script to verify CORS configuration for the enquiries endpoint
"""

import requests
import json

def test_cors_preflight():
    """Test CORS preflight request"""
    url = "https://tmis-business-guru-backend.onrender.com/api/enquiries"
    
    # Test OPTIONS request (preflight)
    headers = {
        'Origin': 'https://tmis-business-guru.vercel.app',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Authorization, Content-Type'
    }
    
    print("🧪 Testing CORS preflight request...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    
    try:
        response = requests.options(url, headers=headers, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower() or 'cors' in key.lower():
                print(f"  {key}: {value}")
        
        if response.status_code == 200:
            print("✅ CORS preflight request successful!")
            return True
        else:
            print(f"❌ CORS preflight failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_actual_request():
    """Test actual GET request with CORS headers"""
    url = "https://tmis-business-guru-backend.onrender.com/api/enquiries"
    
    headers = {
        'Origin': 'https://tmis-business-guru.vercel.app',
        'Authorization': 'Bearer test-token',  # This will fail auth but should pass CORS
        'Content-Type': 'application/json'
    }
    
    print("\n🧪 Testing actual GET request...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers:")
        for key, value in response.headers.items():
            if 'access-control' in key.lower() or 'cors' in key.lower():
                print(f"  {key}: {value}")
        
        # We expect 401 (unauthorized) but CORS should work
        if response.status_code in [401, 422]:  # JWT error is expected
            print("✅ CORS working! (Got expected auth error)")
            return True
        elif response.status_code == 200:
            print("✅ Request successful!")
            return True
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_health_endpoint():
    """Test if the backend is running"""
    url = "https://tmis-business-guru-backend.onrender.com/api/health"
    
    print("🧪 Testing backend health...")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 CORS Fix Verification Test")
    print("=" * 50)
    
    # Test backend health first
    if not test_health_endpoint():
        print("\n❌ Backend is not responding. Please check deployment.")
        exit(1)
    
    # Test CORS preflight
    preflight_success = test_cors_preflight()
    
    # Test actual request
    request_success = test_actual_request()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"  Backend Health: ✅")
    print(f"  CORS Preflight: {'✅' if preflight_success else '❌'}")
    print(f"  Actual Request: {'✅' if request_success else '❌'}")
    
    if preflight_success and request_success:
        print("\n🎉 CORS fix successful! The enquiries endpoint should now work.")
    else:
        print("\n❌ CORS issues still exist. Check the backend configuration.")
