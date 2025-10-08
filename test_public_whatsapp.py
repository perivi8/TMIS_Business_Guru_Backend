import requests
import json

# Test data for the public WhatsApp endpoint
test_data = {
    "mobile_number": "918106811285",
    "wati_name": "Test Public User"
}

# Send POST request to the public WhatsApp endpoint
response = requests.post(
    "http://localhost:5000/api/whatsapp/public-send",
    json=test_data,
    headers={"Content-Type": "application/json"}
)

print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")

# Try to parse JSON if possible
try:
    print(f"Response JSON: {response.json()}")
except:
    print("Response is not valid JSON")