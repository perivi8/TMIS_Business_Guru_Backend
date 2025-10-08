import requests
import json

# Test data simulating an incoming WhatsApp message from GreenAPI
webhook_data = {
    "message": {
        "textMessage": {
            "text": "Hi I am interested!"
        },
        "idMessage": "TEST_MESSAGE_12345"
    },
    "chatId": "918106811285@c.us",
    "senderName": "Test User"
}

# Send POST request to the production webhook endpoint
try:
    response = requests.post(
        "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook",
        json=webhook_data,
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