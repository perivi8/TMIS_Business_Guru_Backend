#!/usr/bin/env python3
"""
Script to find client named 'Hyma' and update their optional mobile number
"""

import os
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    print("❌ MONGODB_URI environment variable not found")
    exit(1)

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client.tmis_business_guru
    # Test connection
    db.command("ping")
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {str(e)}")
    exit(1)

# Find clients named "Hyma"
try:
    results = list(db.clients.find({'legal_name': 'Hyma'}))
    print(f"Found {len(results)} clients named Hyma")
    
    for client_data in results:
        client_id = client_data.get('_id')
        optional_mobile = client_data.get('optional_mobile_number', 'Not set')
        print(f"Client ID: {client_id}, Optional Mobile: {optional_mobile}")
        
        # Update the optional mobile number
        new_mobile = "9876543210"  # Example new number
        result = db.clients.update_one(
            {'_id': client_id},
            {
                '$set': {
                    'optional_mobile_number': new_mobile,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        print(f"Updated client {client_id} with new mobile: {new_mobile}")
        print(f"Matched count: {result.matched_count}, Modified count: {result.modified_count}")
        
except Exception as e:
    print(f"Error searching for clients: {str(e)}")