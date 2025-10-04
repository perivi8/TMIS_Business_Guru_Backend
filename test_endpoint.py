import requests
import json

# Test the forgot-password endpoint
url = "http://localhost:5000/api/forgot-password"
data = {"email": "test@example.com"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
