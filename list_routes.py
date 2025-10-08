import requests

# Get all routes from the Flask application
response = requests.get("http://localhost:5000")

# Print the response
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")