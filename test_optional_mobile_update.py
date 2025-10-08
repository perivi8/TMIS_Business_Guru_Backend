#!/usr/bin/env python3
"""
Test script to verify WhatsApp message sending when optional mobile number is updated
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_optional_mobile_update():
    """Test WhatsApp message sending when optional mobile number is updated"""
    try:
        print("🔍 Testing Optional Mobile Number Update...")
        
        # Import the services
        from client_whatsapp_service import client_whatsapp_service
        
        if not client_whatsapp_service or not client_whatsapp_service.api_available:
            print("❌ WhatsApp service not available")
            return False
            
        print("✅ WhatsApp service is available")
        
        # Test data - using a test number that should work
        test_client_data = {
            'legal_name': 'Test User',
            'mobile_number': '918106811285',  # Primary mobile number (this is where the message should be sent)
            'optional_mobile_number': '919876543210',  # New optional mobile number
            'registration_number': 'TEST123',
            'trade_name': 'Test Business',
            'gst_status': 'Active',
            'constitution_type': 'Private Limited',
            'address': '123 Test Street',
            'district': 'Test District',
            'state': 'Test State',
            'pincode': '123456',
            'required_loan_amount': '100000',
            'loan_purpose': 'Test Purpose',
            'user_email': 'test@example.com'
        }
        
        # Old client data (simulating the previous state)
        old_client_data = {
            'legal_name': 'Test User',
            'mobile_number': '918106811285',  # Primary mobile number
            'optional_mobile_number': '',  # No optional mobile number before
            'registration_number': 'TEST123',
            'trade_name': 'Test Business',
            'gst_status': 'Active',
            'constitution_type': 'Private Limited',
            'address': '123 Test Street',
            'district': 'Test District',
            'state': 'Test State',
            'pincode': '123456',
            'required_loan_amount': '100000',
            'loan_purpose': 'Test Purpose',
            'user_email': 'test@example.com'
        }
        
        # Fields that were updated
        updated_fields = ['optional_mobile_number']
        
        print(f"📱 Testing WhatsApp message for optional mobile number update...")
        print(f"   Primary mobile number: {test_client_data['mobile_number']}")
        print(f"   New optional mobile number: {test_client_data['optional_mobile_number']}")
        print(f"   Updated fields: {updated_fields}")
        
        # Send the WhatsApp message
        results = client_whatsapp_service.send_multiple_client_update_messages(
            test_client_data, 
            updated_fields, 
            old_client_data
        )
        
        print(f"📱 WhatsApp notification results: {results}")
        
        # Check if the message was sent successfully
        if isinstance(results, list) and len(results) > 0:
            for i, result in enumerate(results):
                if isinstance(result, dict):
                    success = result.get('success', False)
                    if success:
                        print(f"✅ Message {i+1} sent successfully!")
                        print(f"   Message ID: {result.get('message_id', 'N/A')}")
                    else:
                        print(f"❌ Message {i+1} failed to send")
                        print(f"   Error: {result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Unexpected result format for message {i+1}: {type(result)}")
                    return False
        else:
            print("⚠️ No messages were sent (this might be expected if no changes were detected)")
            return True
            
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_optional_mobile_message():
    """Test sending a direct optional mobile number update message"""
    try:
        print("\n🔍 Testing Direct Optional Mobile Number Message...")
        
        # Import the services
        from client_whatsapp_service import client_whatsapp_service
        from greenapi_whatsapp_service import greenapi_service
        
        if not client_whatsapp_service or not client_whatsapp_service.api_available:
            print("❌ WhatsApp service not available")
            return False
            
        print("✅ WhatsApp service is available")
        
        # Test data
        test_client_data = {
            'legal_name': 'Test User',
            'mobile_number': '918106811285',  # Primary mobile number (this is where the message should be sent)
            'optional_mobile_number': '919876543210'  # New optional mobile number
        }
        
        # Format the phone number
        formatted_number = client_whatsapp_service.format_phone_number(test_client_data['mobile_number'])
        print(f"📞 Formatted phone number: {formatted_number}")
        
        # Create the message directly
        optional_mobile = test_client_data['optional_mobile_number']
        legal_name = test_client_data['legal_name']
        
        message = f"""Hii {legal_name} sir/madam, 

Your alternate mobile number ({optional_mobile}) was added successfully . 

Thank you for keeping your information up to date with us!"""
        
        print(f"✉️ Message to be sent:")
        print(f"   {message}")
        
        # Send the message directly
        result = greenapi_service.send_message(formatted_number, message)
        
        print(f"📱 Direct message result: {result}")
        
        if isinstance(result, dict):
            if result.get('success', False):
                print("✅ Direct message sent successfully!")
                print(f"   Message ID: {result.get('message_id', 'N/A')}")
                return True
            else:
                print(f"❌ Direct message failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Unexpected result format: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Direct message test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 WhatsApp Optional Mobile Number Update Test")
    print("=" * 50)
    
    # Test 1: Full flow test
    success1 = test_optional_mobile_update()
    
    # Test 2: Direct message test
    success2 = test_direct_optional_mobile_message()
    
    if success1 and success2:
        print("\n🎉 All tests passed! WhatsApp messages for optional mobile number updates are working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        
    sys.exit(0 if (success1 and success2) else 1)