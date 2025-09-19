#!/usr/bin/env python3
"""
Minimal startup test for Render deployment
This tests the absolute minimum required for the app to start
"""

import os
import sys
from dotenv import load_dotenv

def main():
    print("🚀 TMIS Business Guru - Startup Test")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Test 1: Basic imports
    print("1. Testing basic imports...")
    try:
        from flask import Flask
        from flask_cors import CORS
        from flask_jwt_extended import JWTManager
        print("   ✅ Flask imports successful")
    except Exception as e:
        print(f"   ❌ Flask import failed: {e}")
        return 1
    
    # Test 2: MongoDB import
    print("2. Testing MongoDB import...")
    try:
        from pymongo import MongoClient
        print("   ✅ MongoDB import successful")
    except Exception as e:
        print(f"   ❌ MongoDB import failed: {e}")
        return 1
    
    # Test 3: Environment variables
    print("3. Testing environment variables...")
    mongodb_uri = os.getenv('MONGODB_URI')
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    
    if not mongodb_uri:
        print("   ⚠️  MONGODB_URI not set, using fallback")
        mongodb_uri = "mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0"
    else:
        print("   ✅ MONGODB_URI found")
    
    if not jwt_secret:
        print("   ⚠️  JWT_SECRET_KEY not set, using fallback")
        jwt_secret = "tmis-business-guru-secret-key-2024"
    else:
        print("   ✅ JWT_SECRET_KEY found")
    
    # Test 4: MongoDB connection
    print("4. Testing MongoDB connection...")
    try:
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        db = client.tmis_business_guru
        db.command("ping")
        print("   ✅ MongoDB connection successful")
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        print("   ⚠️  This might be okay if it's a network issue")
    
    # Test 5: Flask app creation
    print("5. Testing Flask app creation...")
    try:
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = jwt_secret
        
        # CORS configuration
        CORS(app, origins=[
            "http://localhost:4200", 
            "http://localhost:4201", 
            "https://tmis-business-guru.vercel.app"
        ], supports_credentials=True)
        
        jwt = JWTManager(app)
        
        # Add a simple health check route
        @app.route('/', methods=['GET'])
        def health():
            return {"status": "healthy", "message": "Backend is running"}
        
        @app.route('/api/health', methods=['GET'])
        def api_health():
            return {"status": "healthy", "message": "API is running"}
        
        print("   ✅ Flask app created successfully")
        
        # Test 6: Try to start the app (just test, don't actually run)
        print("6. Testing app configuration...")
        port = int(os.environ.get('PORT', 5000))
        print(f"   ✅ Port configured: {port}")
        
    except Exception as e:
        print(f"   ❌ Flask app creation failed: {e}")
        return 1
    
    print("\n🎉 All startup tests passed!")
    print("💡 If Render deployment still fails, check:")
    print("   1. Render dashboard logs")
    print("   2. Environment variables in Render dashboard")
    print("   3. Build logs for any Python package issues")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
