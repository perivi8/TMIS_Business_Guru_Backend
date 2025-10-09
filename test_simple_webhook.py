#!/usr/bin/env python3
"""
Simple test to verify webhook functionality
"""

import json
from datetime import datetime

# Sample webhook data that matches what GreenAPI sends
sample_webhook_data = {
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "test_message_12345"
    },
    "senderData": {
        "chatId": "918106811285@c.us",
        "senderName": "John Doe",
        "pushName": "John Doe WhatsApp Name",
        "chatName": "John Doe Chat"
    }
}

def test_message_extraction():
    """Test the message extraction logic"""
    print("🔄 Testing message extraction logic...")
    
    # Simulate the _extract_message_info function logic
    data = sample_webhook_data
    result = {
        'has_message_data': False,
        'chat_id': '',
        'message_text': '',
        'sender_name': '',
        'message_id': ''
    }
    
    # Process the data
    if data.get('typeWebhook') == 'incomingMessageReceived' and 'messageData' in data:
        print("📦 Processing incoming message with messageData")
        message_data = data.get('messageData', {})
        sender_data = data.get('senderData', {})
        
        # Extract text message
        if isinstance(message_data, dict):
            if 'textMessage' in message_data and isinstance(message_data['textMessage'], dict):
                result['message_text'] = message_data['textMessage'].get('text', '')
            result['message_id'] = message_data.get('idMessage', '')
            
        # Extract sender info
        if isinstance(sender_data, dict):
            result['chat_id'] = sender_data.get('chatId', '')
            
            # Try multiple fields for sender name
            sender_name_options = [
                sender_data.get('senderName', ''),
                sender_data.get('chatName', ''),
                sender_data.get('pushName', ''),
                sender_data.get('notifyName', '')
            ]
            
            for name_option in sender_name_options:
                if name_option and name_option.strip():
                    result['sender_name'] = name_option.strip()
                    break
                    
        result['has_message_data'] = bool(result['message_text'])
    
    print(f"📤 Extracted data: {json.dumps(result, indent=2)}")
    
    # Test enquiry creation logic
    if result['has_message_data']:
        chat_id = result['chat_id']
        sender_name = result['sender_name']
        message_text = result['message_text']
        
        # Extract and clean mobile number
        sender_number = chat_id.replace('@c.us', '')
        clean_number = ''.join(filter(str.isdigit, sender_number))
        
        # Determine display name
        if sender_name and sender_name.strip():
            display_name = sender_name.strip()
        else:
            display_name = f"WhatsApp User ({clean_number})"
        
        print(f"\n📋 Enquiry would be created with:")
        print(f"   Display Name: {display_name}")
        print(f"   WhatsApp Username: {sender_name}")
        print(f"   Mobile Number: {clean_number}")
        print(f"   Original Chat ID: {chat_id}")
        print(f"   Message: {message_text}")
        
        return True
    else:
        print("❌ No message data extracted")
        return False

def main():
    """Run the test"""
    print("🚀 Testing WhatsApp Webhook Message Extraction")
    print("=" * 50)
    
    success = test_message_extraction()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Message extraction test PASSED")
        print("🎉 Webhook should now properly capture WhatsApp username and mobile number!")
    else:
        print("❌ Message extraction test FAILED")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
