#!/usr/bin/env python3
"""
Manual test to add an enquiry directly to database
This verifies the database connection and enquiry creation logic
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def create_test_enquiry():
    """Create a test enquiry directly in the database"""
    print("🔄 Creating test enquiry in database...")
    
    try:
        # Connect to MongoDB
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("❌ MONGODB_URI not found in environment variables")
            return False
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client.tmis_business_guru
        enquiries_collection = db.enquiries
        
        # Test connection
        client.admin.command('ping')
        print("✅ Database connection successful")
        
        # Create test enquiry (simulating what webhook would create)
        test_enquiry = {
            'date': datetime.utcnow(),
            'wati_name': 'Manual Test User',
            'user_name': 'Manual Test WhatsApp Name',
            'mobile_number': '9876543210',
            'secondary_mobile_number': None,
            'gst': '',
            'gst_status': '',
            'business_type': '',
            'business_nature': '',
            'staff': 'WhatsApp Bot',
            'comments': 'New Enquiry - Interested',
            'additional_comments': 'Received via WhatsApp: "Hi I am interested!" (Manual Test)',
            # WhatsApp specific fields
            'whatsapp_status': 'received',
            'whatsapp_message_id': f'manual_test_{int(datetime.utcnow().timestamp())}',
            'whatsapp_chat_id': '9876543210@c.us',
            'whatsapp_sender_name': 'Manual Test WhatsApp Name',
            'whatsapp_message_text': 'Hi I am interested!',
            'whatsapp_sent': False,
            'source': 'manual_test',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert enquiry
        result = enquiries_collection.insert_one(test_enquiry)
        print(f"✅ Test enquiry created with ID: {result.inserted_id}")
        
        # Verify it was created
        created_enquiry = enquiries_collection.find_one({'_id': result.inserted_id})
        if created_enquiry:
            print("✅ Enquiry verified in database")
            print(f"   Name: {created_enquiry.get('wati_name')}")
            print(f"   Mobile: {created_enquiry.get('mobile_number')}")
            print(f"   WhatsApp Name: {created_enquiry.get('whatsapp_sender_name')}")
            print(f"   Source: {created_enquiry.get('source')}")
        
        # Count total enquiries
        total_count = enquiries_collection.count_documents({})
        whatsapp_count = enquiries_collection.count_documents({'source': {'$regex': 'whatsapp|manual_test'}})
        
        print(f"📊 Database stats:")
        print(f"   Total enquiries: {total_count}")
        print(f"   WhatsApp/Test enquiries: {whatsapp_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test enquiry: {e}")
        return False

def main():
    """Run the manual test"""
    print("🧪 Manual Enquiry Database Test")
    print("="*40)
    
    success = create_test_enquiry()
    
    print("\n" + "="*40)
    if success:
        print("✅ Manual test PASSED")
        print("💡 Database connection and enquiry creation works!")
        print("🎯 The issue is likely the same-number webhook limitation")
        print("\n📱 Next steps:")
        print("   1. Ask someone with a different number to test the WhatsApp link")
        print("   2. Check your enquiries page - the manual test enquiry should appear")
        print("   3. When a real user tests, their enquiry will also appear")
    else:
        print("❌ Manual test FAILED")
        print("🔍 Check database connection and credentials")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
