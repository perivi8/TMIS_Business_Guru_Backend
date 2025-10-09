#!/usr/bin/env python3
"""
Debug script to identify webhook issues
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook_endpoint_accessibility():
    """Test if the webhook endpoint is accessible"""
    print("🔄 Testing webhook endpoint accessibility...")
    
    webhook_url = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook"
    test_url = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook/test"
    
    try:
        # Test the test endpoint first
        response = requests.get(test_url, timeout=10)
        if response.status_code == 200:
            print("✅ Webhook test endpoint is accessible")
            print(f"📋 Response: {response.json()}")
        else:
            print(f"❌ Webhook test endpoint failed: {response.status_code}")
            return False
            
        # Test the actual webhook endpoint with POST
        test_data = {
            "typeWebhook": "incomingMessageReceived",
            "messageData": {
                "textMessage": {
                    "text": "Hi I am interested!"
                },
                "idMessage": "debug_test_123"
            },
            "senderData": {
                "chatId": "919876543210@c.us",  # Different number for testing
                "senderName": "Debug Test User"
            }
        }
        
        response = requests.post(
            webhook_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is accessible and processing data")
            print(f"📋 Response: {response.json()}")
            return True
        else:
            print(f"❌ Webhook endpoint failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook endpoint: {e}")
        return False

def check_greenapi_webhook_config():
    """Check GreenAPI webhook configuration"""
    print("\n🔄 Checking GreenAPI webhook configuration...")
    
    instance_id = os.getenv('GREENAPI_INSTANCE_ID')
    token = os.getenv('GREENAPI_TOKEN')
    
    if not instance_id or not token:
        print("❌ GreenAPI credentials not found in environment")
        return False
    
    try:
        # Get webhook settings
        url = f"https://api.green-api.com/waInstance{instance_id}/getSettings/{token}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            settings = response.json()
            webhook_url = settings.get('webhookUrl', '')
            webhook_url_token = settings.get('webhookUrlToken', '')
            
            print("✅ GreenAPI settings retrieved")
            print(f"📋 Webhook URL: {webhook_url}")
            print(f"📋 Webhook URL Token: {webhook_url_token}")
            
            expected_webhook = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook"
            if webhook_url == expected_webhook:
                print("✅ Webhook URL is correctly configured")
                return True
            else:
                print(f"❌ Webhook URL mismatch!")
                print(f"   Expected: {expected_webhook}")
                print(f"   Actual: {webhook_url}")
                return False
        else:
            print(f"❌ Failed to get GreenAPI settings: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking GreenAPI config: {e}")
        return False

def test_same_number_issue():
    """Test if the issue is with same number messaging"""
    print("\n🔄 Testing same number issue...")
    
    print("📋 Analysis:")
    print("   Your WhatsApp Business number: 918106811285")
    print("   Test message sent from: 8106811285 (same number)")
    print()
    print("🚨 POTENTIAL ISSUE IDENTIFIED:")
    print("   GreenAPI typically does NOT send webhooks for messages")
    print("   sent FROM the same number that owns the WhatsApp Business account.")
    print()
    print("💡 SOLUTION:")
    print("   Ask someone with a DIFFERENT phone number to test the link:")
    print("   https://wa.me/918106811285?text=Hi%20I%20am%20interested!")
    print()
    print("🔍 To verify this theory:")
    print("   1. Check GreenAPI dashboard for incoming message logs")
    print("   2. Look for webhook delivery attempts")
    print("   3. Test with a different phone number")
    
    return True

def check_database_connection():
    """Test database connection and recent enquiries"""
    print("\n🔄 Testing database connection...")
    
    try:
        from pymongo import MongoClient
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("❌ MONGODB_URI not found")
            return False
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client.tmis_business_guru
        enquiries_collection = db.enquiries
        
        # Test connection
        client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Check recent enquiries
        recent_enquiries = list(enquiries_collection.find().sort('created_at', -1).limit(5))
        print(f"📊 Found {len(recent_enquiries)} recent enquiries")
        
        # Check for WhatsApp enquiries specifically
        whatsapp_enquiries = list(enquiries_collection.find({
            'source': 'whatsapp_webhook'
        }).sort('created_at', -1).limit(3))
        
        print(f"📱 Found {len(whatsapp_enquiries)} WhatsApp webhook enquiries")
        
        if whatsapp_enquiries:
            print("📋 Recent WhatsApp enquiries:")
            for enquiry in whatsapp_enquiries:
                print(f"   - {enquiry.get('wati_name', 'Unknown')} ({enquiry.get('mobile_number', 'No number')})")
                print(f"     Created: {enquiry.get('created_at', 'Unknown time')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def provide_testing_recommendations():
    """Provide recommendations for proper testing"""
    print("\n" + "="*60)
    print("🎯 TESTING RECOMMENDATIONS")
    print("="*60)
    
    print("\n1. 🚨 SAME NUMBER ISSUE (Most Likely Cause)")
    print("   Problem: You're testing from the same number (8106811285)")
    print("   Solution: Ask someone with a DIFFERENT number to test")
    print("   Why: GreenAPI doesn't send webhooks for self-messages")
    
    print("\n2. 📱 PROPER TESTING STEPS")
    print("   a) Share this link with a friend/colleague:")
    print("      https://wa.me/918106811285?text=Hi%20I%20am%20interested!")
    print("   b) Ask them to click and send the message")
    print("   c) Check your enquiries page for the new entry")
    
    print("\n3. 🔍 DEBUGGING STEPS")
    print("   a) Check GreenAPI dashboard for webhook logs")
    print("   b) Check Render logs for incoming webhook requests")
    print("   c) Verify webhook URL in GreenAPI settings")
    
    print("\n4. 🧪 ALTERNATIVE TESTING")
    print("   Use the test endpoint to simulate webhook data:")
    print("   POST https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook/test-data")
    
    print("\n5. ✅ SUCCESS INDICATORS")
    print("   - Render logs show: '📥 === NEW WEBHOOK REQUEST ==='")
    print("   - Database gets new enquiry with source: 'whatsapp_webhook'")
    print("   - Frontend shows real-time notification")

def main():
    """Run all debug checks"""
    print("🚀 WhatsApp Webhook Issue Debugging")
    print("="*50)
    
    # Run all checks
    endpoint_ok = test_webhook_endpoint_accessibility()
    greenapi_ok = check_greenapi_webhook_config()
    db_ok = check_database_connection()
    same_number_analysis = test_same_number_issue()
    
    print("\n" + "="*50)
    print("📊 DEBUG RESULTS SUMMARY")
    print("="*50)
    print(f"Webhook Endpoint: {'✅ OK' if endpoint_ok else '❌ ISSUE'}")
    print(f"GreenAPI Config: {'✅ OK' if greenapi_ok else '❌ ISSUE'}")
    print(f"Database: {'✅ OK' if db_ok else '❌ ISSUE'}")
    print(f"Same Number Analysis: {'✅ COMPLETED' if same_number_analysis else '❌ FAILED'}")
    
    provide_testing_recommendations()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
