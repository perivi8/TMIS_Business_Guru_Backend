#!/usr/bin/env python3
"""
Debug script to understand Render startup issues
"""

import os
import sys
import requests

# Set environment variables to mimic Render
os.environ['FLASK_ENV'] = 'production'
os.environ['PORT'] = '5000'

def test_local_startup():
    """Test local app startup to compare with Render"""
    print("=== Testing Local App Startup ===")
    
    try:
        # Import app similar to how it's done in start_server.py
        print("🔄 Importing app...")
        from app import app
        print("✅ App imported successfully")
        
        # Check registered routes
        print("\n=== Checking Registered Routes ===")
        webhook_routes = []
        all_routes = []
        for rule in app.url_map.iter_rules():
            rule_str = str(rule)
            all_routes.append(rule_str)
            if 'webhook' in rule_str.lower():
                webhook_routes.append(rule_str)
        
        print(f"Total routes: {len(all_routes)}")
        print(f"Webhook routes: {len(webhook_routes)}")
        for route in webhook_routes:
            print(f"  ✅ {route}")
            
        if not webhook_routes:
            print("❌ No webhook routes found!")
            
        # Test webhook endpoint locally
        print("\n=== Testing Local Webhook Endpoint ===")
        with app.test_client() as client:
            # Test data
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
            
            response = client.post(
                '/api/enquiries/whatsapp/webhook',
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Local webhook test status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Local webhook endpoint working")
                print(f"Response: {response.get_json()}")
            else:
                print("❌ Local webhook endpoint failed")
                print(f"Response: {response.get_data()}")
                
    except Exception as e:
        print(f"❌ Local startup test failed: {e}")
        import traceback
        traceback.print_exc()

def compare_with_render():
    """Compare local behavior with Render behavior"""
    print("\n=== Comparing with Render ===")
    base_url = "https://tmis-business-guru-backend.onrender.com"
    
    try:
        # Test routes endpoint on Render
        response = requests.get(f"{base_url}/api/test-routes", timeout=30)
        if response.status_code == 200:
            data = response.json()
            api_routes = data.get('api_routes', [])
            webhook_routes = [route for route in api_routes if 'webhook' in route.get('path', '').lower()]
            
            print(f"Render webhook routes: {len(webhook_routes)}")
            for route in webhook_routes:
                print(f"  ❌ {route['path']} ({route['endpoint']})")
                
            if not webhook_routes:
                print("❌ No webhook routes found on Render")
        else:
            print(f"❌ Failed to get routes from Render: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Render comparison failed: {e}")

if __name__ == "__main__":
    test_local_startup()
    compare_with_render()