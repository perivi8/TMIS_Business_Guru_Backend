#!/usr/bin/env python3
"""
Test script to debug the download endpoint issue
"""
import requests
import json
import sys

# Test configuration
BASE_URL = "http://localhost:5000"
CLIENT_ID = "68ce36a78228dfe5dd76ebbc"
DOCUMENT_TYPE = "ie_code_document"

def test_download_endpoint():
    """Test the download endpoint that's causing 500 errors"""
    
    print(f"🔍 Testing download endpoint...")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Document Type: {DOCUMENT_TYPE}")
    print(f"URL: {BASE_URL}/api/clients/{CLIENT_ID}/download/{DOCUMENT_TYPE}")
    
    # First, let's test without authentication to see what happens
    try:
        print("\n📡 Testing without authentication...")
        response = requests.get(f"{BASE_URL}/api/clients/{CLIENT_ID}/download/{DOCUMENT_TYPE}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}")
        
    except Exception as e:
        print(f"❌ Error without auth: {e}")
    
    # Test the client details endpoint to see if client exists
    try:
        print(f"\n📡 Testing client details endpoint...")
        response = requests.get(f"{BASE_URL}/api/clients/{CLIENT_ID}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}")
        
    except Exception as e:
        print(f"❌ Error getting client details: {e}")
    
    # Test basic connectivity
    try:
        print(f"\n📡 Testing basic connectivity...")
        response = requests.get(f"{BASE_URL}/api/clients/test")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error with basic connectivity: {e}")

if __name__ == "__main__":
    test_download_endpoint()
