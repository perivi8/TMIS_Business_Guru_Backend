#!/usr/bin/env python3
"""
Deployment Test Script for TMIS Business Guru Backend
This script tests all critical components before deployment
"""

import os
import sys
from dotenv import load_dotenv

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'MONGODB_URI',
        'JWT_SECRET_KEY',
        'FLASK_ENV',
        'SMTP_EMAIL',
        'SMTP_PASSWORD',
        'SMTP_SERVER',
        'SMTP_PORT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: NOT SET")
        else:
            if 'PASSWORD' in var or 'SECRET' in var or 'URI' in var:
                print(f"✅ {var}: {'*' * 10} (hidden)")
            else:
                print(f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All environment variables are set")
        return True

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🔍 Testing MongoDB Connection...")
    
    try:
        from pymongo import MongoClient
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            # Use fallback
            mongodb_uri = "mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0"
            print("⚠️  Using fallback MongoDB URI")
        
        print(f"MongoDB URI: {mongodb_uri[:50]}...{mongodb_uri[-20:]}")
        
        client = MongoClient(mongodb_uri)
        db = client.tmis_business_guru
        
        # Test connection
        db.command("ping")
        print("✅ MongoDB connection successful")
        
        # Test collections
        collections = db.list_collection_names()
        print(f"📊 Available collections: {collections}")
        
        # Test basic operations
        users_count = db.users.count_documents({})
        clients_count = db.clients.count_documents({})
        print(f"👥 Users in database: {users_count}")
        print(f"🏢 Clients in database: {clients_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {str(e)}")
        print("🔧 Troubleshooting tips:")
        print("1. Check if MongoDB Atlas cluster is running")
        print("2. Verify IP whitelist includes 0.0.0.0/0 for Render")
        print("3. Check MongoDB URI format and credentials")
        return False

def test_flask_imports():
    """Test if all Flask dependencies can be imported"""
    print("\n🔍 Testing Flask Dependencies...")
    
    try:
        from flask import Flask, request, jsonify
        from flask_cors import CORS
        from flask_jwt_extended import JWTManager
        from werkzeug.utils import secure_filename
        import bcrypt
        import PyPDF2
        import cloudinary
        print("✅ All Flask dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_app_creation():
    """Test if Flask app can be created"""
    print("\n🔍 Testing Flask App Creation...")
    
    try:
        from flask import Flask
        from flask_cors import CORS
        from flask_jwt_extended import JWTManager
        
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test-key')
        
        CORS(app, origins=["https://tmis-business-guru.vercel.app"], supports_credentials=True)
        jwt = JWTManager(app)
        
        print("✅ Flask app created successfully")
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {str(e)}")
        return False

def test_backend_deployment():
    """Test the deployed backend endpoints"""
    print("\n🔍 Testing Backend Deployment...")
    
    base_url = "https://tmis-business-guru-backend.onrender.com"
    
    try:
        import requests
        
        # Test 1: Health check
        try:
            response = requests.get(f"{base_url}/", timeout=10)
            print(f"✅ Health Check: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Message: {data.get('message')}")
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return False
        
        # Test 2: API Health
        try:
            response = requests.get(f"{base_url}/api/health", timeout=10)
            print(f"✅ API Health: {response.status_code}")
        except Exception as e:
            print(f"❌ API Health Failed: {e}")
            return False
        
        # Test 3: CORS preflight test
        try:
            headers = {
                'Origin': 'https://tmis-business-guru.vercel.app',
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Authorization,Content-Type'
            }
            response = requests.options(f"{base_url}/api/clients", headers=headers, timeout=10)
            print(f"✅ CORS Preflight: {response.status_code}")
        except Exception as e:
            print(f"❌ CORS Preflight Failed: {e}")
        
        print("✅ Backend deployment tests completed")
        return True
        
    except ImportError:
        print("❌ requests library not available for deployment testing")
        return False
    except Exception as e:
        print(f"❌ Backend deployment test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 TMIS Business Guru Backend Deployment Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Flask Dependencies", test_flask_imports),
        ("Flask App Creation", test_app_creation),
        ("MongoDB Connection", test_mongodb_connection),
        ("Backend Deployment", test_backend_deployment),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Backend is ready for deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    import requests
    sys.exit(main())
