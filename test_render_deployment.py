#!/usr/bin/env python3
"""
Test script to verify Render deployment and webhook functionality
"""

import requests
import json
import time

def test_render_deployment():
    """Test if the Render deployment is working correctly"""
    base_url = "https://tmis-business-guru-backend.onrender.com"
    
    print(f"=== Testing Render Deployment ===")
    print(f"Base URL: {base_url}")
    
    # Test 1: Health check endpoint
    print("\n🔄 Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=30)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check endpoint working")
            print(f"Response: {response.json()}")
        else:
            print("❌ Health check endpoint failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
    
    # Test 2: Test routes endpoint
    print("\n🔄 Testing routes endpoint...")
    try:
        response = requests.get(f"{base_url}/api/test-routes", timeout=30)
        print(f"Routes test status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Routes test endpoint working")
            data = response.json()
            print(f"Total routes: {data.get('total_routes', 'N/A')}")
            print(f"API routes count: {data.get('api_routes_count', 'N/A')}")
            
            # Check if webhook route is registered
            api_routes = data.get('api_routes', [])
            webhook_routes = [route for route in api_routes if 'webhook' in route.get('path', '')]
            if webhook_routes:
                print("✅ Webhook routes found in registration:")
                for route in webhook_routes:
                    print(f"  - {route['path']} ({route['endpoint']})")
            else:
                print("❌ No webhook routes found in registration")
        else:
            print("❌ Routes test endpoint failed")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Routes test failed with error: {e}")
    
    # Test 3: Try to access the webhook endpoint directly
    print("\n🔄 Testing webhook endpoint accessibility...")
    try:
        # Send a simple OPTIONS request to check if the endpoint exists
        response = requests.options(f"{base_url}/api/enquiries/whatsapp/webhook", timeout=30)
        print(f"Webhook OPTIONS status: {response.status_code}")
        if response.status_code in [200, 405]:  # 405 is also acceptable (method not allowed)
            print("✅ Webhook endpoint is accessible")
        else:
            print("❌ Webhook endpoint is not accessible")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Webhook endpoint test failed with error: {e}")
    
    # Test 4: Send a test webhook payload
    print("\n🔄 Testing webhook functionality...")
    webhook_data = {
        "message": {
            "textMessage": {
                "text": "Hi I am interested!"
            },
            "idMessage": "TEST_MESSAGE_12345"
        },
        "chatId": "918106811285@c.us",
        "senderName": "Test User"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/enquiries/whatsapp/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Webhook POST status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook endpoint is working correctly")
            print(f"Response: {response.json()}")
        elif response.status_code == 404:
            print("❌ Webhook endpoint not found (404)")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Webhook endpoint returned error: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Webhook functionality test failed with error: {e}")

if __name__ == "__main__":
    test_render_deployment()