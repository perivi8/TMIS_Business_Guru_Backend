import requests
import json

# Test data simulating what GreenAPI might actually send for a real user message
# This is based on typical GreenAPI webhook format for incoming messages
real_greenapi_data = {
    "typeWebhook": "incomingMessageReceived",
    "instanceData": {
        "idInstance": "7105335459",
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1728498946,
    "senderData": {
        "chatId": "919876543210@c.us",  # User's WhatsApp number
        "senderName": "Real User Name",  # User's name
        "chatName": "Real User Name"
    },
    "messageData": {
        "typeMessage": "textMessage",
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "A9B6F90E3D2F1A4B5C6D7E8F0G1H2I3J"
    }
}

# Send POST request to the production webhook endpoint
try:
    response = requests.post(
        "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook",
        json=real_greenapi_data,
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