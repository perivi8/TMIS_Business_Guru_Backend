import requests
import json

# Test data for the WhatsApp endpoint
test_data = {
    "mobile_number": "918106811285"
}

# Send POST request to the WhatsApp test endpoint
response = requests.post(
    "http://localhost:5000/api/enquiries/whatsapp/test",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
try:
    print(f"Response: {response.json()}")
except:
    print(f"Response Text: {response.text}")