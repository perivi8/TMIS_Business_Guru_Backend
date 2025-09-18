#!/usr/bin/env python3
"""
Startup validation script for TMIS Business Guru Backend
Run this before starting the application to validate all requirements
"""

import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if all required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        'MONGODB_URI',
        'JWT_SECRET_KEY',
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_USER',
        'EMAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            logger.error(f"❌ {var} is not set")
        else:
            logger.info(f"✅ {var} is configured")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Check JWT secret is not default
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if jwt_secret in ['your-secret-key-change-this-in-production', 'your-secret-key-here']:
        logger.error("❌ JWT_SECRET_KEY is using default value - please change it!")
        return False
    
    logger.info("✅ All environment variables are properly configured")
    return True

def check_mongodb_connection():
    """Test MongoDB connection"""
    logger.info("🔍 Testing MongoDB connection...")
    
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            logger.error("❌ MONGODB_URI not set")
            return False
        
        # Hide credentials in logs
        safe_uri = mongodb_uri.split('@')[0] + '@***'
        logger.info(f"📍 Connecting to: {safe_uri}")
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Test database access
        db = client.tmis_business_guru
        collections = db.list_collection_names()
        logger.info(f"📚 Available collections: {collections}")
        
        # Check if required collections exist
        required_collections = ['users', 'clients']
        for collection in required_collections:
            if collection in collections:
                count = db[collection].count_documents({})
                logger.info(f"✅ {collection} collection: {count} documents")
            else:
                logger.warning(f"⚠️  {collection} collection not found (will be created automatically)")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        return False

def check_required_packages():
    """Check if all required Python packages are installed"""
    logger.info("🔍 Checking required packages...")
    
    required_packages = [
        'flask',
        'flask_cors',
        'flask_jwt_extended',
        'pymongo',
        'bcrypt',
        'python-dotenv',
        'gunicorn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is not installed")
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {missing_packages}")
        logger.info("💡 Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required packages are installed")
    return True

def check_port_availability():
    """Check if the required port is available"""
    logger.info("🔍 Checking port configuration...")
    
    port = os.getenv('PORT', '5000')
    logger.info(f"📍 Application will run on port: {port}")
    
    try:
        port_int = int(port)
        if port_int < 1 or port_int > 65535:
            logger.error(f"❌ Invalid port number: {port}")
            return False
        logger.info("✅ Port configuration is valid")
        return True
    except ValueError:
        logger.error(f"❌ Invalid port value: {port}")
        return False

def main():
    """Run all startup checks"""
    logger.info("🚀 Starting TMIS Business Guru Backend Validation")
    logger.info("=" * 60)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Required Packages", check_required_packages),
        ("MongoDB Connection", check_mongodb_connection),
        ("Port Configuration", check_port_availability)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        logger.info(f"\n📋 {check_name}")
        logger.info("-" * 40)
        
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            logger.error(f"❌ {check_name} check failed with exception: {str(e)}")
            all_passed = False
    
    logger.info("\n" + "=" * 60)
    
    if all_passed:
        logger.info("🎉 All checks passed! Backend is ready to start.")
        return 0
    else:
        logger.error("💥 Some checks failed. Please fix the issues before starting the backend.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
