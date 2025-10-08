#!/usr/bin/env python3
"""
Test script to verify Gemini AI integration for document processing
"""

import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test if Gemini AI is properly configured and accessible"""
    print("🔍 Testing Gemini AI Integration...")
    
    # Check if API key exists
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    try:
        # Configure Gemini AI
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test with a simple prompt
        test_prompt = """
        Extract the following information from this sample GST text and return as JSON:
        - registration_number
        - legal_name
        - address
        
        Sample text: "GSTIN: 27AABCU9603R1ZX Legal Name of Business: ABC PRIVATE LIMITED Address: 123 Business Street, Mumbai"
        
        Return only valid JSON.
        """
        
        response = model.generate_content(test_prompt)
        
        if response and response.text:
            print("✅ Gemini AI is working correctly!")
            print(f"📄 Sample response: {response.text[:200]}...")
            return True
        else:
            print("❌ No response from Gemini AI")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini AI: {e}")
        return False

def test_document_processor():
    """Test the DocumentProcessor class"""
    print("\n🔍 Testing DocumentProcessor class...")
    
    try:
        from document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        print("✅ DocumentProcessor initialized successfully")
        
        if processor.use_ai:
            print("✅ DocumentProcessor is configured to use Gemini AI")
        else:
            print("⚠️ DocumentProcessor is using regex fallback (AI not available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing DocumentProcessor: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 TMIS Business Guru - Gemini AI Integration Test")
    print("=" * 50)
    
    # Test Gemini connection
    gemini_ok = test_gemini_connection()
    
    # Test DocumentProcessor
    processor_ok = test_document_processor()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Gemini AI Connection: {'✅ PASS' if gemini_ok else '❌ FAIL'}")
    print(f"   DocumentProcessor:    {'✅ PASS' if processor_ok else '❌ FAIL'}")
    
    if gemini_ok and processor_ok:
        print("\n🎉 All tests passed! The AI integration is ready to use.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Please check the configuration.")
        sys.exit(1)
