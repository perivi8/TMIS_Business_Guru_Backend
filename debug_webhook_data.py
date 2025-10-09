import sys
import os

# Set environment variables to mimic production
os.environ['FLASK_ENV'] = 'production'
os.environ['MONGODB_URI'] = 'mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0'
os.environ['JWT_SECRET_KEY'] = 'tmis-business-guru-secret-key-2024'

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enquiry_routes import _extract_message_info

# Test with data that might be sent by a real user
real_user_data = {
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {
        "idInstance": 7105335459,
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1728498946,
    "senderData": {
        "chatId": "919876543210@c.us",  # This would be the user's number
        "senderName": "John Doe",       # This would be the user's name
        "chatName": "John Doe"
    },
    "messageData": {
        "typeMessage": "textMessage",
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "A9B6F90E3D2F1A4B5C6D7E8F0G1H2I3J"
    }
}

# Test with same number data (what you're actually testing with)
same_number_data = {
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {
        "idInstance": 7105335459,
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1728498946,
    "senderData": {
        "chatId": "918106811285@c.us",  # Same as business number
        "senderName": "Your Name",       # Your WhatsApp name
        "chatName": "Your Name"
    },
    "messageData": {
        "typeMessage": "textMessage",
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "SAME_NUMBER_TEST_123"
    }
}
print("=== Debugging Webhook Data Extraction ===")
print(f"Input data keys: {list(real_user_data.keys())}")
print(f"typeWebhook: {real_user_data.get('typeWebhook')}")
print(f"messageData in data: {'messageData' in real_user_data}")
print(f"message in data: {'message' in real_user_data}")

# Test the extraction function with different number
print("\n=== Testing with DIFFERENT number (should work) ===")
result = _extract_message_info(real_user_data)
print(f"Extracted result: {result}")

# Test with same number
print("\n=== Testing with SAME number (your test case) ===")
result_same = _extract_message_info(same_number_data)
print(f"Extracted result: {result_same}")

# Check conditions manually
print("\n=== Manual Condition Check ===")
print(f"Condition 1 (Format 2): typeWebhook == 'incomingMessageReceived' and 'messageData' in data")
print(f"  typeWebhook == 'incomingMessageReceived': {real_user_data.get('typeWebhook') == 'incomingMessageReceived'}")
print(f"  'messageData' in data: {'messageData' in real_user_data}")

print(f"Condition 2 (Format 3): typeWebhook == 'incomingMessageReceived' and 'message' in data")
print(f"  typeWebhook == 'incomingMessageReceived': {real_user_data.get('typeWebhook') == 'incomingMessageReceived'}")
print(f"  'message' in data: {'message' in real_user_data}")

# Important note about same number issue
print("\n=== IMPORTANT ANALYSIS ===")
print("🚨 LIKELY ISSUE: You're testing from the SAME number (8106811285)")
print("💡 GreenAPI typically does NOT send webhooks for messages from the same number")
print("✅ SOLUTION: Ask someone with a DIFFERENT phone number to test the link")
print("📱 Test link: https://wa.me/918106811285?text=Hi%20I%20am%20interested!")