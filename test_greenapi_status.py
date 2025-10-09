#!/usr/bin/env python3
"""
Test GreenAPI connection and settings
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_greenapi_status():
    """Test GreenAPI instance status"""
    instance_id = os.getenv('GREENAPI_INSTANCE_ID')
    token = os.getenv('GREENAPI_TOKEN')
    
    print(f"🔄 Testing GreenAPI Instance: {instance_id}")
    
    try:
        # Get instance status
        url = f"https://api.green-api.com/waInstance{instance_id}/getStateInstance/{token}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Instance Status: {status.get('stateInstance', 'Unknown')}")
            
            if status.get('stateInstance') == 'authorized':
                print("✅ WhatsApp is authorized and ready")
            else:
                print("❌ WhatsApp is not authorized - scan QR code")
                
        else:
            print(f"❌ Failed to get status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_greenapi_settings():
    """Test GreenAPI webhook settings"""
    instance_id = os.getenv('GREENAPI_INSTANCE_ID')
    token = os.getenv('GREENAPI_TOKEN')
    
    print(f"\n🔄 Testing GreenAPI Settings...")
    
    try:
        # Get settings
        url = f"https://api.green-api.com/waInstance{instance_id}/getSettings/{token}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            settings = response.json()
            
            print(f"✅ Settings retrieved")
            print(f"📋 Webhook URL: {settings.get('webhookUrl', 'Not set')}")
            print(f"📋 Incoming messages: {settings.get('incomingWebhook', 'Not set')}")
            print(f"📋 Outgoing messages: {settings.get('outgoingWebhook', 'Not set')}")
            
            # Check if webhook is properly configured
            expected_url = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook"
            if settings.get('webhookUrl') == expected_url:
                print("✅ Webhook URL is correctly configured")
            else:
                print(f"❌ Webhook URL mismatch!")
                
            if settings.get('incomingWebhook') == 'yes':
                print("✅ Incoming webhook notifications are enabled")
            else:
                print("❌ Incoming webhook notifications are disabled")
                
        else:
            print(f"❌ Failed to get settings: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🚀 GreenAPI Connection Test")
    print("="*40)
    
    test_greenapi_status()
    test_greenapi_settings()
    
    print("\n" + "="*40)
    print("💡 If WhatsApp is authorized and webhook settings are correct,")
    print("   ask your friend to send the message again!")

if __name__ == "__main__":
    main()
