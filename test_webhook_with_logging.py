import requests
import json

# Test data that should work with the current implementation
test_data = {
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "TEST_MESSAGE_12345"
    },
    "senderData": {
        "chatId": "919876543210@c.us",
        "senderName": "John Doe"
    }
}

# Send POST request to the production webhook endpoint
try:
    response = requests.post(
        "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook",
        json=test_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    try:
        print(f"Response JSON: {response.json()}")
    except:
        print("Response is not valid JSON")
        
except Exception as e:
    print(f"Error: {str(e)}")