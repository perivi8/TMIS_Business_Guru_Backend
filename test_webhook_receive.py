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

# Send POST request to the webhook endpoint
response = requests.post(
    "http://localhost:5000/api/enquiries/whatsapp/webhook",
    json=webhook_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")