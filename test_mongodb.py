#!/usr/bin/env python3
"""
MongoDB Connection Test Script
Tests the MongoDB Atlas connection with the current .env configuration
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB Atlas connection and display database information"""
    
    print("=== MONGODB CONNECTION TEST ===")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Get MongoDB URI from environment
    mongodb_uri = os.getenv('MONGODB_URI')
    
    if not mongodb_uri:
        print("❌ ERROR: MONGODB_URI not found in environment variables")
        return False
    
    print(f"MongoDB URI: {mongodb_uri}")
    print()
    
    try:
        # Create MongoDB client
        print("🔄 Connecting to MongoDB Atlas...")
        client = MongoClient(mongodb_uri)
        
        # Test connection with ping
        print("🔄 Testing connection with ping...")
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        print()
        
        # Get database
        db = client.tmis_business_guru
        print(f"📊 Connected to database: {db.name}")
        print()
        
        # List collections
        collections = db.list_collection_names()
        print(f"📁 Collections found: {len(collections)}")
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        print()
        
        # Test basic operations
        print("🧪 Testing basic database operations...")
        
        # Test users collection
        if 'users' in collections:
            users_count = db.users.count_documents({})
            print(f"  👥 Users collection: {users_count} users")
            
            # Sample user (without password)
            sample_user = db.users.find_one({}, {'password': 0})
            if sample_user:
                print(f"  📝 Sample user: {sample_user.get('email', 'No email')} ({sample_user.get('role', 'No role')})")
        
        # Test clients collection
        if 'clients' in collections:
            clients_count = db.clients.count_documents({})
            print(f"  🏢 Clients collection: {clients_count} clients")
            
            # Sample client
            sample_client = db.clients.find_one({})
            if sample_client:
                print(f"  📝 Sample client: {sample_client.get('legal_name', 'No name')} ({sample_client.get('status', 'No status')})")
        
        # Test enquiries collection
        if 'enquiries' in collections:
            enquiries_count = db.enquiries.count_documents({})
            print(f"  📞 Enquiries collection: {enquiries_count} enquiries")
        
        print()
        print("✅ All database operations successful!")
        
        # Close connection
        client.close()
        print("🔒 Connection closed")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print()
        print("🔍 Troubleshooting tips:")
        print("1. Check if MongoDB URI includes database name")
        print("2. Verify MongoDB Atlas cluster is running")
        print("3. Check network connectivity")
        print("4. Verify MongoDB Atlas IP whitelist settings")
        print("5. Check username/password credentials")
        
        return False

def main():
    """Main function"""
    success = test_mongodb_connection()
    
    if success:
        print("\n🎉 MongoDB connection test PASSED!")
        print("Your backend should be able to connect to MongoDB Atlas successfully.")
    else:
        print("\n💥 MongoDB connection test FAILED!")
        print("Please fix the connection issues before deploying.")
    
    return success

if __name__ == "__main__":
    main()
