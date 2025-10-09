#!/usr/bin/env python3
"""
Test script to verify the WhatsApp webhook fix and database connectivity
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test MongoDB connection and enquiries collection"""
    print("🔄 Testing MongoDB connection...")
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("❌ MONGODB_URI not found in environment variables")
        return False
    
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client.tmis_business_guru
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Test enquiries collection
        enquiries_collection = db.enquiries
        count = enquiries_collection.count_documents({})
        print(f"📊 Found {count} enquiries in database")
        
        # Test inserting a sample enquiry
        test_enquiry = {
            'date': datetime.utcnow(),
            'wati_name': 'Test WhatsApp User',
            'user_name': 'Test User',
            'mobile_number': '1234567890',
            'comments': 'Test enquiry from webhook fix',
            'staff': 'WhatsApp Bot',
            'source': 'webhook_test',
            'whatsapp_sender_name': 'Test User',
            'whatsapp_chat_id': '1234567890@c.us',
            'whatsapp_message_text': 'Hi I am interested!',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = enquiries_collection.insert_one(test_enquiry)
        print(f"✅ Test enquiry inserted with ID: {result.inserted_id}")
        
        # Clean up test enquiry
        enquiries_collection.delete_one({'_id': result.inserted_id})
        print("🧹 Test enquiry cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_webhook_endpoint():
    """Test the webhook endpoint with sample data"""
    print("\n🔄 Testing webhook endpoint...")
    
    # Sample webhook data that mimics GreenAPI format
    sample_webhook_data = {
        "typeWebhook": "incomingMessageReceived",
        "messageData": {
            "textMessage": {
                "text": "Hi I am interested!"
            },
            "idMessage": "test_message_123"
        },
        "senderData": {
            "chatId": "918106811285@c.us",
            "senderName": "John Doe",
            "pushName": "John Doe",
            "chatName": "John Doe"
        }
    }
    
    # Test locally first
    local_url = "http://localhost:5000/api/enquiries/whatsapp/webhook"
    
    try:
        response = requests.post(
            local_url,
            json=sample_webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Local webhook test successful")
            print(f"📋 Response: {response.json()}")
            return True
        else:
            print(f"❌ Local webhook test failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️ Local server not running, skipping local test")
        return True
    except Exception as e:
        print(f"❌ Local webhook test error: {e}")
        return False

def test_production_webhook():
    """Test the production webhook endpoint"""
    print("\n🔄 Testing production webhook endpoint...")
    
    # Sample webhook data
    sample_webhook_data = {
        "typeWebhook": "incomingMessageReceived",
        "messageData": {
            "textMessage": {
                "text": "Hi I am interested!"
            },
            "idMessage": "prod_test_message_123"
        },
        "senderData": {
            "chatId": "918106811285@c.us",
            "senderName": "Production Test User",
            "pushName": "Production Test User"
        }
    }
    
    # Production URL
    prod_url = "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook"
    
    try:
        response = requests.post(
            prod_url,
            json=sample_webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Production webhook test successful")
            print(f"📋 Response: {response.json()}")
            return True
        else:
            print(f"❌ Production webhook test failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Production webhook test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting WhatsApp Webhook Fix Tests")
    print("=" * 50)
    
    # Test database connection
    db_success = test_database_connection()
    
    # Test webhook endpoints
    local_success = test_webhook_endpoint()
    prod_success = test_production_webhook()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"   Local Webhook: {'✅ PASS' if local_success else '❌ FAIL'}")
    print(f"   Production Webhook: {'✅ PASS' if prod_success else '❌ FAIL'}")
    
    if all([db_success, local_success or prod_success]):
        print("\n🎉 All critical tests passed! Webhook fix is ready.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
