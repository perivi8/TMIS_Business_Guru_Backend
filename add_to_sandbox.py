#!/usr/bin/env python3
"""
WhatsApp Sandbox Number Management Script
Helps add phone numbers to WhatsApp Business API sandbox for testing
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_sandbox_status():
    """Check current sandbox configuration"""
    print("🔍 Checking WhatsApp Sandbox Configuration...")
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    if not access_token or not phone_number_id:
        print("❌ Missing WhatsApp credentials in .env file")
        return False
    
    print(f"✅ Access Token: {'*' * 20}{access_token[-10:] if len(access_token) > 10 else access_token}")
    print(f"✅ Phone Number ID: {phone_number_id}")
    
    return True

def test_number(phone_number):
    """Test if a phone number can receive WhatsApp messages"""
    print(f"\n🧪 Testing WhatsApp message to: {phone_number}")
    
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': phone_number,
        'type': 'text',
        'text': {
            'body': '🧪 Test message from TMIS Business Guru - Sandbox verification'
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        
        if response.status_code == 200:
            message_id = result.get('messages', [{}])[0].get('id', 'Unknown')
            print(f"✅ SUCCESS! Message sent to {phone_number}")
            print(f"📋 Message ID: {message_id}")
            return True
        else:
            error_data = result.get('error', {})
            error_message = error_data.get('message', 'Unknown error')
            
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"📋 Error: {error_message}")
            
            # Provide specific solutions
            if 'not in allowed list' in error_message.lower():
                print(f"🔧 SOLUTION: Add {phone_number} to Facebook sandbox recipients")
                print("   1. Go to https://developers.facebook.com/")
                print("   2. Select your WhatsApp Business app")
                print("   3. Click 'WhatsApp' → 'Getting Started'")
                print(f"   4. Add {phone_number} to recipient list")
                print("   5. Verify with WhatsApp code")
            elif 'access token' in error_message.lower():
                print("🔧 SOLUTION: Generate new access token")
                print("   1. Go to Facebook Developer Console")
                print("   2. Generate new temporary access token")
                print("   3. Update WHATSAPP_ACCESS_TOKEN in .env file")
            
            return False
            
    except Exception as e:
        print(f"❌ Network Error: {str(e)}")
        return False

def main():
    """Main function"""
    print("🌍 WhatsApp Sandbox Number Management")
    print("=" * 50)
    
    if not check_sandbox_status():
        return
    
    # Test numbers
    test_numbers = [
        "918106811285",  # Your working number
        "919876543210",  # Example test number
    ]
    
    print(f"\n📱 Testing {len(test_numbers)} phone numbers...")
    
    working_numbers = []
    failed_numbers = []
    
    for number in test_numbers:
        if test_number(number):
            working_numbers.append(number)
        else:
            failed_numbers.append(number)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 30)
    print(f"✅ Working Numbers: {len(working_numbers)}")
    for num in working_numbers:
        print(f"   • {num}")
    
    print(f"\n❌ Failed Numbers: {len(failed_numbers)}")
    for num in failed_numbers:
        print(f"   • {num} (needs sandbox approval)")
    
    if failed_numbers:
        print(f"\n🔧 TO FIX FAILED NUMBERS:")
        print("1. Go to: https://developers.facebook.com/")
        print("2. Select your WhatsApp Business app")
        print("3. Navigate: WhatsApp → Getting Started")
        print("4. Find: 'Add recipient phone number' section")
        print("5. Add each failed number:")
        for num in failed_numbers:
            print(f"   • {num}")
        print("6. Verify each number with WhatsApp code")
        print("7. Re-run this script to test")
    
    print(f"\n🎯 NEXT STEPS:")
    if len(working_numbers) > 0:
        print("✅ You can test WhatsApp with working numbers")
        print("✅ Create enquiries with working numbers")
    
    if len(failed_numbers) > 0:
        print("⚠️  Add failed numbers to sandbox for testing")
        print("⚠️  Or move to production for unlimited numbers")
    
    print("\n🚀 For production deployment:")
    print("   • Complete Facebook Business verification")
    print("   • Submit app for WhatsApp Business API review")
    print("   • Get dedicated business phone number")

if __name__ == "__main__":
    main()
