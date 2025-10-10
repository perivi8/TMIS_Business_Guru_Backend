import sys
import os
from unittest.mock import Mock, patch

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_quota_handling():
    """Test quota handling for reply options"""
    print("Testing quota handling for reply options...")
    print("=" * 50)
    
    # Mock a quota exceeded response
    quota_exceeded_result = {
        'success': False,
        'error': 'Monthly quota has been exceeded',
        'status_code': 466
    }
    
    # Mock a normal success response
    success_result = {
        'success': True,
        'message_id': 'test_message_123'
    }
    
    # Test cases
    test_cases = [
        ("Get Loan", quota_exceeded_result),
        ("Check Eligibility", quota_exceeded_result),
        ("More Details", success_result)
    ]
    
    for message_text, result in test_cases:
        print(f"Testing message: '{message_text}'")
        print(f"  Result: {result}")
        
        # Check if it's a quota exceeded error
        error_msg = result.get('error', '').lower()
        status_code = result.get('status_code', 0)
        
        is_quota_exceeded = 'quota exceeded' in error_msg or 'monthly quota' in error_msg or status_code == 466
        print(f"  Is quota exceeded: {is_quota_exceeded}")
        
        if is_quota_exceeded:
            print(f"  ⚠️ Quota exceeded for '{message_text}' - logging warning but returning success to webhook")
        elif result['success']:
            print(f"  ✅ Reply sent successfully for '{message_text}'")
        else:
            print(f"  ❌ Error sending reply for '{message_text}': {result.get('error')}")
        
        print()

if __name__ == "__main__":
    test_quota_handling()