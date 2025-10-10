#!/usr/bin/env python3
"""
Simple verification script for the WhatsApp welcome message implementation
"""

import sys
import os

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from greenapi_whatsapp_service import whatsapp_service

def verify_welcome_message():
    """Verify that the welcome message template is correctly implemented"""
    print("🔍 Verifying WhatsApp welcome message implementation...")
    
    if not whatsapp_service:
        print("❌ WhatsApp service not available")
        return
    
    # Get the message templates
    templates = whatsapp_service.get_message_templates()
    welcome_template = templates.get('new_enquiry', '')
    
    print("📄 Welcome message template:")
    print("-" * 40)
    print(welcome_template)
    print("-" * 40)
    
    # Check for required elements
    required_elements = [
        "Hi {wati_name}👋 Welcome to Business Guru Loans!",
        "Get ₹10 Lakhs in 24 hours for your business",
        "✅ 1% monthly interest (Lowest in market!)",
        "✅ Zero collateral or CIBIL checks",
        "✅ New startups welcome",
        "Apply Now: https://tmis-business-guru.vercel.app/new-enquiry",
        "✨ Special Benefits:",
        "0% processing fees (First 50 applicants)",
        "Flexible repayment: 1-5 years",
        "🏆 Trusted by 2,500+ businesses",
        "📱 Ready to grow?",
        "Your success journey begins now! 🚀",
        "*Please click on any option below:*",
        "🔗 Get Loan: https://wa.me/918106811285?text=Get%20Loan",
        "🔗 Check Eligibility: https://wa.me/918106811285?text=Check%20Eligibility",
        "🔗 More Details: https://wa.me/918106811285?text=More%20Details"
    ]
    
    print("\n✅ Verification Results:")
    print("=" * 40)
    
    all_passed = True
    for element in required_elements:
        if element in welcome_template:
            print(f"✅ Found: {element[:50]}...")
        else:
            print(f"❌ Missing: {element[:50]}...")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All required elements are present in the welcome message template!")
    else:
        print("\n⚠️ Some required elements are missing.")
    
    # Test message formatting
    print("\n📝 Testing message formatting...")
    test_enquiry = {
        'wati_name': 'John Doe',
        'business_nature': 'Retail Store'
    }
    
    # Format the message
    try:
        formatted_message = welcome_template.format(
            wati_name=test_enquiry.get('wati_name', 'Customer'),
            business_nature=test_enquiry.get('business_nature', 'your business')
        )
        
        print("✅ Message formatting successful!")
        print(f"📝 Formatted message preview (first 200 chars):")
        print(formatted_message[:200] + "..." if len(formatted_message) > 200 else formatted_message)
        
    except Exception as e:
        print(f"❌ Message formatting failed: {e}")

if __name__ == "__main__":
    verify_welcome_message()