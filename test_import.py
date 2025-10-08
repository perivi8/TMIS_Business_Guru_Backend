#!/usr/bin/env python3
"""
Test script to check if client_routes.py can be imported successfully
"""

import sys
import os
import traceback

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enquiry_routes import handle_incoming_whatsapp
    print("✅ Successfully imported handle_incoming_whatsapp")
    print(f"Function: {handle_incoming_whatsapp}")
    print(f"Function name: {handle_incoming_whatsapp.__name__}")
except Exception as e:
    print(f"❌ Failed to import handle_incoming_whatsapp: {e}")
    traceback.print_exc()

print("=== IMPORT TEST ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {[f for f in os.listdir('.') if f.endswith('.py')]}")

# Test individual imports
print("\n=== TESTING INDIVIDUAL IMPORTS ===")

try:
    print("1. Testing Flask imports...")
    from flask import Blueprint, request, jsonify, current_app, send_file
    print("✅ Flask imports successful")
except Exception as e:
    print(f"❌ Flask imports failed: {e}")

try:
    print("2. Testing JWT imports...")
    from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
    print("✅ JWT imports successful")
except Exception as e:
    print(f"❌ JWT imports failed: {e}")

try:
    print("3. Testing MongoDB imports...")
    from pymongo import MongoClient
    from bson import ObjectId
    from bson.json_util import dumps
    print("✅ MongoDB imports successful")
except Exception as e:
    print(f"❌ MongoDB imports failed: {e}")

try:
    print("4. Testing Cloudinary imports...")
    import cloudinary
    import cloudinary.uploader
    print("✅ Cloudinary imports successful")
except Exception as e:
    print(f"❌ Cloudinary imports failed: {e}")

try:
    print("5. Testing other imports...")
    from werkzeug.utils import secure_filename
    import os
    import sys
    from datetime import datetime
    import json
    from dotenv import load_dotenv
    import traceback
    print("✅ Other imports successful")
except Exception as e:
    print(f"❌ Other imports failed: {e}")

# Test client_routes import
print("\n=== TESTING CLIENT_ROUTES IMPORT ===")
try:
    print("Attempting to import client_routes...")
    import client_routes
    print("✅ client_routes imported successfully")
    
    if hasattr(client_routes, 'client_bp'):
        print(f"✅ client_bp found: {client_routes.client_bp}")
        print(f"Blueprint name: {client_routes.client_bp.name}")
    else:
        print("❌ client_bp not found in module")
        
except ImportError as e:
    print(f"❌ ImportError: {e}")
    print(f"Traceback: {traceback.format_exc()}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    print(f"Traceback: {traceback.format_exc()}")

print("\n=== TEST COMPLETE ===")
