#!/usr/bin/env python3
"""
Simple test script for the Gemini Chatbot Service
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test if all required environment variables are set"""
    print("=== Testing Environment Variables ===")
    
    required_vars = ['GEMINI_API_KEY', 'MONGODB_URI']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-10:] if len(value) > 10 else value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("\n✅ All environment variables are set")
    return True

def test_gemini_import():
    """Test if Google Generative AI can be imported"""
    print("\n=== Testing Gemini AI Import ===")
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
        
        # Test API key configuration
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Failed to import Google Generative AI: {e}")
        print("   Run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Failed to configure Gemini API: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n=== Testing MongoDB Connection ===")
    
    try:
        from pymongo import MongoClient
        
        mongodb_uri = os.getenv('MONGODB_URI')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # Test database access
        db = client.tmis_business_guru
        collections = db.list_collection_names()
        print(f"✅ Database access successful. Collections: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_chatbot_service():
    """Test the Gemini Chatbot Service"""
    print("\n=== Testing Gemini Chatbot Service ===")
    
    try:
        from gemini_chatbot_service import gemini_chatbot_service
        
        if gemini_chatbot_service is None:
            print("❌ Gemini Chatbot Service is None")
            return False
        
        print("✅ Gemini Chatbot Service imported successfully")
        
        # Test basic functionality
        try:
            stats = gemini_chatbot_service.get_enquiry_stats()
            print(f"✅ Enquiry stats retrieved: {stats}")
        except Exception as e:
            print(f"⚠️ Warning: Could not get enquiry stats: {e}")
        
        try:
            stats = gemini_chatbot_service.get_client_stats()
            print(f"✅ Client stats retrieved: {stats}")
        except Exception as e:
            print(f"⚠️ Warning: Could not get client stats: {e}")
        
        # Test AI response generation
        try:
            response = gemini_chatbot_service.generate_response("Hello, how many enquiries do we have?")
            print(f"✅ AI response generated successfully (length: {len(response)} chars)")
            print(f"   Sample: {response[:100]}...")
        except Exception as e:
            print(f"❌ Failed to generate AI response: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Gemini Chatbot Service: {e}")
        return False
    except Exception as e:
        print(f"❌ Gemini Chatbot Service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 TMIS Gemini Chatbot Service Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_gemini_import,
        test_mongodb_connection,
        test_chatbot_service
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Chatbot service is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
