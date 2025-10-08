#!/usr/bin/env python3
"""
Direct GreenAPI Test - Check connection and send test message
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_greenapi():
    """Test GreenAPI directly with your credentials"""
    
    instance_id = os.getenv('CHATAPI_INSTANCE_ID')  # 7105335459
    token = os.getenv('CHATAPI_TOKEN')  # 3a0876a6822049bc...
    
    print("🧪 Direct GreenAPI Test")
    print("=" * 40)
    print(f"Instance ID: {instance_id}")
    print(f"Token: {token[:20]}...")
    
    base_url = f"https://{instance_id}.api.greenapi.com"
    print(f"Base URL: {base_url}")
    
    # Test 1: Check instance state
    print(f"\n📡 Testing instance state...")
    try:
        state_url = f"{base_url}/waInstance{instance_id}/getStateInstance/{token}"
        print(f"State URL: {state_url}")
        
        response = requests.get(state_url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ State Response: {json.dumps(data, indent=2)}")
            
            state = data.get('stateInstance', 'unknown')
            if state == 'authorized':
                print(f"✅ Instance is AUTHORIZED - ready to send messages!")
                
                # Test 2: Send test message
                print(f"\n📤 Testing message sending...")
                send_test_message(base_url, instance_id, token)
                
            else:
                print(f"⚠️ Instance state: {state}")
                print(f"💡 You may need to scan QR code again")
        else:
            print(f"❌ Failed to get state: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking state: {str(e)}")

def send_test_message(base_url, instance_id, token):
    """Send a test message"""
    try:
        # Send to your own number first
        send_url = f"{base_url}/waInstance{instance_id}/sendMessage/{token}"
        
        test_data = {
            "chatId": "918106811285@c.us",  # Your own number
            "message": "🧪 GreenAPI Test - This message was sent without OTP!"
        }
        
        print(f"Send URL: {send_url}")
        print(f"Payload: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(send_url, json=test_data, timeout=30)
        print(f"Send Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Message sent successfully!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('idMessage'):
                print(f"📋 Message ID: {data['idMessage']}")
                print(f"🎉 SUCCESS! Check your WhatsApp for the test message!")
                
                # Now test with other numbers
                test_other_numbers(base_url, instance_id, token)
            else:
                print(f"⚠️ No message ID returned")
        else:
            print(f"❌ Failed to send message: {response.text}")
            
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")

def test_other_numbers(base_url, instance_id, token):
    """Test with other numbers (the ones that failed with Facebook API)"""
    print(f"\n🎯 Testing with numbers that failed Facebook API...")
    
    test_numbers = [
        ('917010905730', 'Your test number'),
        ('919876543210', 'Random test number')
    ]
    
    for number, description in test_numbers:
        print(f"\n📱 Testing {number} ({description})...")
        
        try:
            send_url = f"{base_url}/waInstance{instance_id}/sendMessage/{token}"
            
            test_data = {
                "chatId": f"{number}@c.us",
                "message": f"🎉 SUCCESS! GreenAPI sent this message to {number} WITHOUT OTP verification!"
            }
            
            response = requests.post(send_url, json=test_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('idMessage'):
                    print(f"✅ SUCCESS! Message sent to {number}")
                    print(f"📋 Message ID: {data['idMessage']}")
                    print(f"🎉 NO OTP REQUIRED!")
                else:
                    print(f"⚠️ Response: {data}")
            else:
                print(f"❌ Failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_greenapi()
