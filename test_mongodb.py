#!/usr/bin/env python3
"""
Test MongoDB connection script
Run this to verify your MongoDB Atlas connection is working
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    try:
        # Get MongoDB URI from environment
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("❌ MONGODB_URI environment variable not set")
            return False
        
        print(f"🔗 Connecting to MongoDB Atlas...")
        print(f"📍 URI: {mongodb_uri.split('@')[0]}@***")  # Hide credentials
        
        # Create client and connect
        client = MongoClient(mongodb_uri)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client.tmis_business_guru
        
        # List collections
        collections = db.list_collection_names()
        print(f"📚 Available collections: {collections}")
        
        # Test basic operations
        users_count = db.users.count_documents({})
        clients_count = db.clients.count_documents({})
        
        print(f"👥 Users in database: {users_count}")
        print(f"🏢 Clients in database: {clients_count}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing MongoDB Connection...")
    print("=" * 50)
    
    success = test_mongodb_connection()
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed! MongoDB is ready.")
    else:
        print("💥 Connection failed. Check your .env file and MongoDB Atlas setup.")
