#!/usr/bin/env python3
"""
Check GreenAPI plan limitations and capabilities
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_greenapi_plan():
    """Check GreenAPI plan and limitations"""
    instance_id = os.getenv('GREENAPI_INSTANCE_ID')
    token = os.getenv('GREENAPI_TOKEN')
    
    print("🔍 Checking GreenAPI Plan and Limitations")
    print("="*50)
    
    try:
        # Get account info
        url = f"https://api.green-api.com/waInstance{instance_id}/getAccountInfo/{token}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            account_info = response.json()
            print("✅ Account Information:")
            print(f"   Plan: {account_info.get('tariff', 'Unknown')}")
            print(f"   State: {account_info.get('stateInstance', 'Unknown')}")
            print(f"   Phone: {account_info.get('wid', 'Unknown')}")
            
            # Check if it's a free plan
            tariff = account_info.get('tariff', '').lower()
            if 'free' in tariff or 'trial' in tariff or tariff == 'developer':
                print("\n🚨 FREE/TRIAL PLAN DETECTED!")
                print("   Limitations:")
                print("   - Limited webhook functionality")
                print("   - Restricted sender information")
                print("   - May not receive all webhook events")
                print("   - Limited message quota")
                
        else:
            print(f"❌ Failed to get account info: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_webhook_capabilities():
    """Check what webhook data we can actually get"""
    print("\n🔍 Checking Webhook Capabilities")
    print("="*30)
    
    print("📋 For FREE GreenAPI plans:")
    print("   ✅ Basic message text - Usually available")
    print("   ❓ Sender phone number - May be limited")
    print("   ❓ Sender name/contact info - Often restricted")
    print("   ❓ Full webhook events - May be limited")
    
    print("\n📋 For PAID GreenAPI plans:")
    print("   ✅ Full message text")
    print("   ✅ Complete sender phone number")
    print("   ✅ Sender name and contact info")
    print("   ✅ All webhook events")
    print("   ✅ Higher message quotas")

def suggest_solutions():
    """Suggest solutions for free plan limitations"""
    print("\n💡 SOLUTIONS FOR FREE PLAN")
    print("="*30)
    
    print("🔧 Option 1: Work with Limited Data")
    print("   - Extract phone number from chat ID only")
    print("   - Use generic names like 'WhatsApp User (phone)' ")
    print("   - Still capture enquiries, just with less detail")
    
    print("\n🔧 Option 2: Upgrade to Paid Plan")
    print("   - Get full sender information")
    print("   - Complete webhook functionality")
    print("   - Higher message quotas")
    print("   - Better reliability")
    
    print("\n🔧 Option 3: Alternative Approach")
    print("   - Use WhatsApp Business API directly")
    print("   - Try other WhatsApp API providers")
    print("   - Manual enquiry collection")

def test_actual_webhook_data():
    """Test what data we actually get from webhooks"""
    print("\n🧪 TESTING ACTUAL WEBHOOK DATA")
    print("="*35)
    
    print("📱 Next steps:")
    print("1. Deploy the enhanced logging code")
    print("2. Ask friend to send message again")
    print("3. Check Render logs to see ACTUAL data received")
    print("4. Compare with expected format")
    
    print("\n🔍 What to look for in logs:")
    print("   - 📥 === NEW WEBHOOK REQUEST ===")
    print("   - Raw webhook data from GreenAPI")
    print("   - Available fields in the data")
    print("   - Missing fields (name, contact info)")

def main():
    check_greenapi_plan()
    check_webhook_capabilities()
    suggest_solutions()
    test_actual_webhook_data()
    
    print("\n" + "="*50)
    print("🎯 RECOMMENDATION:")
    print("Deploy the enhanced logging first to see what")
    print("data GreenAPI free plan actually provides!")

if __name__ == "__main__":
    main()
