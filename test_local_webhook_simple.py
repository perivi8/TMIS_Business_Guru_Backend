import os
import sys

# Set environment variables to mimic production
os.environ['FLASK_ENV'] = 'production'
os.environ['MONGODB_URI'] = 'mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0'
os.environ['JWT_SECRET_KEY'] = 'tmis-business-guru-secret-key-2024'

from app import app

# Test data
state_change_data = {
    "typeWebhook": "stateInstanceChanged",
    "instanceData": {
        "idInstance": 710533549,
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1759864577,
    "stateInstance": "starting"
}

incoming_message_data = {
    "typeWebhook": "incomingMessageReceived",
    "message": {
        "type": "text",
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "id": "MESSAGE_ID_12345"
    },
    "senderData": {
        "chatId": "918106811285@c.us",
        "senderName": "Test User"
    }
}

print("=== Testing Local Webhook Handler ===")

with app.test_client() as client:
    # Test state change notification
    print("\n--- Testing State Change Notification ---")
    response = client.post(
        '/api/enquiries/whatsapp/webhook',
        json=state_change_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")
    
    # Test proper incoming message
    print("\n--- Testing Proper Incoming Message ---")
    response = client.post(
        '/api/enquiries/whatsapp/webhook',
        json=incoming_message_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")
    
    # Test test endpoint
    print("\n--- Testing Test Endpoint ---")
    response = client.get('/api/enquiries/whatsapp/webhook/test')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.get_json()}")