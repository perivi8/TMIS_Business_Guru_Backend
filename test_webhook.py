import requests
import json

# Test data for the webhook
test_data = {
    "message": {
        "textMessage": {
            "text": "Hi I am interested!"
        }
    },
    "chatId": "919876543210@c.us"
}

# Send POST request to the webhook endpoint
response = requests.post(
    "http://localhost:5000/api/enquiries/whatsapp/webhook",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")