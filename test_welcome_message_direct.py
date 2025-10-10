#!/usr/bin/env python3
"""
Test script to verify welcome message functionality directly
"""

import sys
import os

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from greenapi_whatsapp_service import whatsapp_service
from datetime import datetime

def test_welcome_message_direct():
    """Test sending a welcome message directly"""
    
    if not whatsapp_service or not whatsapp_service.api_available:
        print("❌ WhatsApp service not available")
        return
    
    # Create a test enquiry data
    test_enquiry = {
        'wati_name': 'Test User',
        'mobile_number': '918106811285',  # Using the business number for testing
        'business_nature': 'Test Business'
    }
    
    print("🚀 Testing welcome message sending...")
    
    # Send the welcome message
    result = whatsapp_service.send_enquiry_message(test_enquiry, 'new_enquiry')
    
    print(f"✅ Result: {result}")
    
    if result['success']:
        print("✅ Welcome message sent successfully!")
    else:
        print(f"❌ Failed to send welcome message: {result.get('error')}")

if __name__ == "__main__":
    test_welcome_message_direct()