#!/usr/bin/env python3
"""
Test script for Client WhatsApp Service
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_whatsapp_service():
    """Test the WhatsApp service functionality"""
    try:
        # Import the client WhatsApp service
        from client_whatsapp_service import client_whatsapp_service
        
        if not client_whatsapp_service.api_available:
            print("❌ WhatsApp service not available")
            return False
        
        print("✅ WhatsApp service is available")
        
        # Test data for a new client
        test_client_data = {
            'legal_name': 'John Doe',
            'mobile_number': '919876543210',  # Replace with a valid test number
            'registration_number': 'REG123456',
            'trade_name': 'Doe Enterprises',
            'gst_status': 'Active',
            'constitution_type': 'Private Limited',
            'address': '123 Main Street',
            'district': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'required_loan_amount': '500000',
            'loan_purpose': 'Business Expansion',
            'ie_code': 'IE123456',
            'website': 'www.doeenterprises.com',
            'user_email': 'john.doe@example.com'
        }
        
        print("📱 Testing new client WhatsApp message...")
        result = client_whatsapp_service.send_new_client_message(test_client_data)
        print(f"Result: {result}")
        
        if result['success']:
            print("✅ New client WhatsApp message sent successfully")
        else:
            print(f"❌ Failed to send new client WhatsApp message: {result.get('error')}")
            
        # Test client update message
        print("\n📱 Testing client update WhatsApp message...")
        update_result = client_whatsapp_service.send_client_update_message(
            test_client_data, 
            'personal_info', 
            ['legal_name', 'address']
        )
        print(f"Update result: {update_result}")
        
        if update_result['success']:
            print("✅ Client update WhatsApp message sent successfully")
        else:
            print(f"❌ Failed to send client update WhatsApp message: {update_result.get('error')}")
            
        # Test loan approved message
        print("\n📱 Testing loan approved WhatsApp message...")
        loan_result = client_whatsapp_service.send_loan_approved_message(test_client_data)
        print(f"Loan approved result: {loan_result}")
        
        if loan_result['success']:
            print("✅ Loan approved WhatsApp message sent successfully")
        else:
            print(f"❌ Failed to send loan approved WhatsApp message: {loan_result.get('error')}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing WhatsApp service: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Client WhatsApp Service...")
    success = test_whatsapp_service()
    if success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)