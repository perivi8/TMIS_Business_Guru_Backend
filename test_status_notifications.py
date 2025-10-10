import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_status_notifications():
    """Test status notifications for reply options"""
    print("Testing status notifications for reply options...")
    print("=" * 50)
    
    # Mock successful message sending result
    success_result = {
        'success': True,
        'message_id': 'test_message_12345'
    }
    
    # Mock failed message sending result
    error_result = {
        'success': False,
        'error': 'Network error occurred',
        'status_code': 500
    }
    
    # Mock quota exceeded result
    quota_result = {
        'success': False,
        'error': 'Monthly quota has been exceeded',
        'status_code': 466
    }
    
    # Test cases
    test_cases = [
        ("Get Loan", success_result, "success"),
        ("Check Eligibility", error_result, "error"),
        ("More Details", quota_result, "quota_exceeded")
    ]
    
    for message_text, result, expected_status in test_cases:
        print(f"Testing message: '{message_text}'")
        print(f"  Result: {result}")
        
        if result['success']:
            print(f"  ✅ Reply sent successfully for '{message_text}'")
            print(f"  📡 Emitting success notification via SocketIO")
            notification = {
                'type': 'webhook_status',
                'status': 'success',
                'message': f"✅ WhatsApp reply sent successfully for '{message_text}'",
                'details': {
                    'message_type': 'reply_option',
                    'option_selected': message_text,
                    'recipient': '918106811285@c.us',
                    'message_id': result.get('message_id', 'unknown')
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            print(f"  Notification: {notification['message']}")
        else:
            error_msg = result.get('error', 'Unknown error')
            status_code = result.get('status_code', 0)
            
            is_quota_exceeded = 'quota exceeded' in error_msg.lower() or status_code == 466
            
            if is_quota_exceeded:
                print(f"  ⚠️ Quota exceeded for '{message_text}'")
                print(f"  📡 Emitting error notification via SocketIO")
                notification = {
                    'type': 'webhook_status',
                    'status': 'error',
                    'message': f"❌ Failed to send WhatsApp reply for '{message_text}': {error_msg}",
                    'details': {
                        'message_type': 'reply_option',
                        'option_selected': message_text,
                        'recipient': '918106811285@c.us',
                        'error': error_msg
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                print(f"  Notification: {notification['message']}")
                print(f"  Note: Still returning success to webhook to prevent webhook errors")
            else:
                print(f"  ❌ Error sending reply for '{message_text}': {error_msg}")
                print(f"  📡 Emitting error notification via SocketIO")
                notification = {
                    'type': 'webhook_status',
                    'status': 'error',
                    'message': f"❌ Failed to send WhatsApp reply for '{message_text}': {error_msg}",
                    'details': {
                        'message_type': 'reply_option',
                        'option_selected': message_text,
                        'recipient': '918106811285@c.us',
                        'error': error_msg
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                print(f"  Notification: {notification['message']}")
        
        print()

if __name__ == "__main__":
    test_status_notifications()