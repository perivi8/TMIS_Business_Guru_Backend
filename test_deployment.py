#!/usr/bin/env python3
"""
TMIS Business Guru - Deployment Test Script
This script tests all critical components before deployment
"""

import os
import sys
import traceback
from datetime import datetime

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'MONGODB_URI',
        'JWT_SECRET_KEY',
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
        else:
            # Hide sensitive values
            if 'PASSWORD' in var or 'SECRET' in var or 'URI' in var:
                print(f"  ✅ {var}: {'*' * 8}...{value[-4:] if len(value) > 4 else '****'}")
            else:
                print(f"  ✅ {var}: {value}")
    
    if missing_vars:
        print(f"  ❌ Missing variables: {', '.join(missing_vars)}")
        return False
    else:
        print("  ✅ All environment variables are set")
        return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🔍 Testing Module Imports...")
    
    modules_to_test = [
        'flask',
        'flask_cors',
        'flask_jwt_extended',
        'pymongo',
        'bcrypt',
        'dotenv',
        'bson',
        'werkzeug'
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"  ❌ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print("  ✅ All required modules can be imported")
        return True

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🔍 Testing MongoDB Connection...")
    
    try:
        from pymongo import MongoClient
        from dotenv import load_dotenv
        
        load_dotenv()
        
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("  ❌ MONGODB_URI not found in environment variables")
            return False
        
        print(f"  🔄 Connecting to MongoDB...")
        client = MongoClient(mongodb_uri)
        db = client.tmis_business_guru
        
        # Test connection
        db.command("ping")
        print("  ✅ MongoDB connection successful")
        
        # Test collections
        users_collection = db.users
        clients_collection = db.clients
        
        user_count = users_collection.count_documents({})
        client_count = clients_collection.count_documents({})
        
        print(f"  📊 Database stats: {user_count} users, {client_count} clients")
        return True
        
    except Exception as e:
        print(f"  ❌ MongoDB connection failed: {str(e)}")
        return False

def test_app_startup():
    """Test if the Flask app can start"""
    print("\n🔍 Testing Flask App Startup...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from app import app
        print("  ✅ Flask app imported successfully")
        
        # Test app configuration
        print(f"  📋 JWT Secret Key: {'*' * 8}...{app.config['JWT_SECRET_KEY'][-4:]}")
        print(f"  📋 Upload Folder: {app.config['UPLOAD_FOLDER']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Flask app startup failed: {str(e)}")
        print(f"  📋 Traceback: {traceback.format_exc()}")
        return False

def test_blueprint_imports():
    """Test if blueprints can be imported"""
    print("\n🔍 Testing Blueprint Imports...")
    
    blueprint_tests = {
        'client_routes': 'client_bp',
        'enquiry_routes': 'enquiry_bp'
    }
    
    results = {}
    for module_name, blueprint_name in blueprint_tests.items():
        try:
            module = __import__(module_name)
            blueprint = getattr(module, blueprint_name)
            print(f"  ✅ {module_name}.{blueprint_name} imported successfully")
            results[module_name] = True
        except ImportError as e:
            print(f"  ❌ {module_name} import failed: {e}")
            results[module_name] = False
        except AttributeError as e:
            print(f"  ❌ {module_name}.{blueprint_name} not found: {e}")
            results[module_name] = False
        except Exception as e:
            print(f"  ❌ {module_name} unexpected error: {e}")
            results[module_name] = False
    
    return all(results.values())

def main():
    """Run all tests"""
    print("🚀 TMIS Business Guru - Deployment Test")
    print("=" * 50)
    print(f"📅 Test Time: {datetime.utcnow().isoformat()}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Module Imports", test_imports),
        ("MongoDB Connection", test_mongodb_connection),
        ("Flask App Startup", test_app_startup),
        ("Blueprint Imports", test_blueprint_imports)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Ready for deployment!")
        print("✅ Your application should work correctly on Render")
    else:
        print("⚠️ SOME TESTS FAILED - Fix issues before deployment")
        print("❌ Application may not work correctly on Render")
    
    print("=" * 50)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
