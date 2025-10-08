import requests
import json

# Test data simulating a state change notification (should be ignored)
state_change_data = {
    "typeWebhook": "stateInstanceChanged",
    "instanceData": {
        "idInstance": 710533549,
        "wid": "918106811285@c.us",
        "typeInstance": "whatsapp"
    },
    "timestamp": 1759864577,
    "stateInstance": "starting"
}

# Send POST request to the production webhook endpoint
try:
    response = requests.post(
        "https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook",
        json=state_change_data,
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