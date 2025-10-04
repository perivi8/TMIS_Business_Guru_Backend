#!/usr/bin/env python3
"""
Debug script to check available endpoints
"""

import requests
import json

def test_endpoints():
    """Test available endpoints"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing Available Endpoints")
    print("=" * 50)
    
    # Test endpoints without auth
    endpoints_to_test = [
        "/api/enquiries/test",
        "/api/whatsapp/test", 
        "/api/whatsapp/templates"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n📡 Testing: {endpoint}")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   Error: {str(e)}")
    
    # Test POST endpoints
    print(f"\n📡 Testing POST: /api/whatsapp/test")
    try:
        data = {
            "mobile_number": "9876543210",
            "wati_name": "Test User",
            "message_type": "new_enquiry"
        }
        response = requests.post(
            f"{base_url}/api/whatsapp/test", 
            json=data,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   Error: {str(e)}")

if __name__ == "__main__":
    test_endpoints()
