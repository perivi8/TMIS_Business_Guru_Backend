#!/usr/bin/env python3
"""
Test the outgoing message webhook format
"""

import requests
import json

# The exact data structure from your logs
test_data = {
    "typeWebhook": "outgoingMessageReceived",
    "instanceData": {
        "idInstance": 7105335459,
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1759988843,
    "idMessage": "3EB04F816622538FD8287C",
    "senderData": {
        "chatId": "918106811285@c.us",
        "chatName": "",
        "sender": "918106811285@c.us",
        "senderName": "",
        "senderContactName": ""
    },
    "messageData": {
        "typeMessage": "textMessage",
        "textMessageData": {
            "textMessage": "Hi I am interested!"
        }
    }
}

def test_webhook_processing():
    """Test how the webhook processes this data"""
    print("🧪 Testing outgoing message webhook processing...")
    
    url = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook"
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json() if response.status_code == 200 else response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ SUCCESS: Webhook processed successfully!")
                if 'enquiry_id' in result:
                    print(f"📝 Enquiry created with ID: {result['enquiry_id']}")
                else:
                    print("ℹ️ Webhook processed but no enquiry created (might be non-interested message)")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP ERROR: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_webhook_processing()
