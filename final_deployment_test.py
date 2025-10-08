#!/usr/bin/env python3
"""
Final deployment test to verify webhook functionality
"""

import os
import sys
import requests
import time

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_local_webhook():
    """Test webhook functionality locally"""
    print("=== Testing Local Webhook ===")
    
    try:
        # Import app
        from app import app
        
        # Test data simulating an incoming WhatsApp message from GreenAPI
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
        
        # Test with Flask test client
        with app.test_client() as client:
            response = client.post(
                '/api/enquiries/whatsapp/webhook',
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Local webhook test status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Local webhook working correctly")
                data = response.get_json()
                print(f"Response: {data}")
                return True
            else:
                print("❌ Local webhook failed")
                print(f"Response: {response.get_data()}")
                return False
                
    except Exception as e:
        print(f"❌ Local webhook test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_webhook():
    """Test webhook functionality on Render"""
    print("\n=== Testing Render Webhook ===")
    
    base_url = "https://tmis-business-guru-backend.onrender.com"
    
    # Test data simulating an incoming WhatsApp message from GreenAPI
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
        # First check if the endpoint exists with OPTIONS request
        print("🔄 Testing endpoint accessibility...")
        response = requests.options(
            f"{base_url}/api/enquiries/whatsapp/webhook",
            timeout=30
        )
        print(f"OPTIONS request status: {response.status_code}")
        
        # Then test the actual POST request
        print("🔄 Testing webhook functionality...")
        response = requests.post(
            f"{base_url}/api/enquiries/whatsapp/webhook",
            json=webhook_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Render webhook test status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Render webhook working correctly")
            data = response.json()
            print(f"Response: {data}")
            return True
        elif response.status_code == 404:
            print("❌ Render webhook endpoint not found")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ Render webhook returned error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Render webhook test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Final Deployment Test")
    print(f"Base directory: {os.getcwd()}")
    
    # Test local webhook
    local_success = test_local_webhook()
    
    # Test Render webhook
    render_success = test_render_webhook()
    
    print("\n=== Test Results ===")
    print(f"Local webhook: {'✅ PASS' if local_success else '❌ FAIL'}")
    print(f"Render webhook: {'✅ PASS' if render_success else '❌ FAIL'}")
    
    if local_success and not render_success:
        print("\n⚠️  Local tests pass but Render tests fail!")
        print("   This suggests a deployment issue on Render.")
        print("   Please redeploy your application to Render.")
    elif local_success and render_success:
        print("\n🎉 All tests pass! Webhook is working correctly.")
        print("   You can now configure the webhook in GreenAPI dashboard:")
        print("   1. Go to https://console.green-api.com")
        print("   2. Select your instance (Instance ID: 7105335459)")
        print("   3. Navigate to Settings > Webhooks")
        print("   4. Set Webhook URL to: https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook")
        print("   5. Enable 'Incoming Message' webhook")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()