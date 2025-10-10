#!/usr/bin/env python3
"""
Test script to verify welcome message functionality
"""

import requests
import json
from datetime import datetime

def test_welcome_message():
    """Test sending a welcome message when 'Hi I am interested!' is received"""
    
    # Simulate the webhook payload that GreenAPI would send
    webhook_data = {
        "typeWebhook": "incomingMessageReceived",
        "messageData": {
            "text": "Hi I am interested!",
            "textMessage": {
                "text": "Hi I am interested!"
            },
            "idMessage": f"test_message_{datetime.now().timestamp()}"
        },
        "senderData": {
            "chatId": "919876543210@c.us",
            "senderName": "Test User"
        }
    }
    
    # Send the test request to the webhook endpoint
    url = "http://localhost:5000/api/enquiries/whatsapp/webhook"
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(webhook_data))
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test successful - welcome message should be sent")
        else:
            print("❌ Test failed - check the response above")
            
    except Exception as e:
        print(f"❌ Error testing welcome message: {str(e)}")

if __name__ == "__main__":
    test_welcome_message()