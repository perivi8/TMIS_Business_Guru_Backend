import sys
import os
import json
from unittest.mock import Mock, patch

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions we need to test
from enquiry_routes import _extract_message_info

def test_message_extraction():
    """Test the message extraction functionality with different formats"""
    print("Testing message extraction...")
    print("=" * 50)
    
    # Test case 1: Format 2 - Incoming message received format with messageData
    test_data_format2 = {
        "typeWebhook": "incomingMessageReceived",
        "messageData": {
            "textMessage": {
                "text": "Get Loan"
            },
            "idMessage": "TEST_MESSAGE_12345"
        },
        "senderData": {
            "chatId": "918106811285@c.us",
            "senderName": "Test User"
        }
    }
    
    print("Testing Format 2 (messageData with textMessage):")
    result = _extract_message_info(test_data_format2)
    print(f"Extracted info: {result}")
    print()
    
    # Test case 2: Format 3 - Incoming message received format with direct message
    test_data_format3 = {
        "typeWebhook": "incomingMessageReceived",
        "message": {
            "textMessage": {
                "text": "Check Eligibility"
            },
            "idMessage": "TEST_MESSAGE_67890"
        },
        "senderData": {
            "chatId": "918106811285@c.us",
            "senderName": "Test User"
        }
    }
    
    print("Testing Format 3 (direct message with textMessage):")
    result = _extract_message_info(test_data_format3)
    print(f"Extracted info: {result}")
    print()
    
    # Test case 3: Format 4 - Direct text format
    test_data_format4 = {
        "typeWebhook": "incomingMessageReceived",
        "text": "More Details",
        "idMessage": "TEST_MESSAGE_11111",
        "senderData": {
            "chatId": "918106811285@c.us",
            "senderName": "Test User"
        }
    }
    
    print("Testing Format 4 (direct text format):")
    result = _extract_message_info(test_data_format4)
    print(f"Extracted info: {result}")
    print()

if __name__ == "__main__":
    test_message_extraction()