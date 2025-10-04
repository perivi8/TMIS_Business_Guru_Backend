import requests
import json

# Test with a registered email (use an email that exists in your database)
url = "http://localhost:5000/api/forgot-password"

# Test with non-existent email first
print("=== Testing with non-existent email ===")
data = {"email": "nonexistent@example.com"}
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
print()

# Test with registered email (replace with actual registered email)
print("=== Testing with registered email ===")
# Using actual email from database
registered_email = "tmis.periviharikrishna@gmail.com"  # Actual registered email
data = {"email": registered_email}
response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
