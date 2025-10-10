import requests
import json

# Test data for "Get Loan" reply
get_loan_data = {
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
        "textMessage": {
            "text": "Get Loan"
        },
        "idMessage": "TEST_GET_LOAN_12345"
    },
    "senderData": {
        "chatId": "918106811285@c.us",
        "senderName": "Test User"
    }
}

# Test data for "Check Eligibility" reply
check_eligibility_data = {
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
        "textMessage": {
            "text": "Check Eligibility"
        },
        "idMessage": "TEST_CHECK_ELIGIBILITY_12345"
    },
    "senderData": {
        "chatId": "918106811285@c.us",
        "senderName": "Test User"
    }
}

# Test data for "More Details" reply
more_details_data = {
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
        "textMessage": {
            "text": "More Details"
        },
        "idMessage": "TEST_MORE_DETAILS_12345"
    },
    "senderData": {
        "chatId": "918106811285@c.us",
        "senderName": "Test User"
    }
}

# Test URLs - adjust as needed for your setup
webhook_url = "http://localhost:5000/api/enquiries/whatsapp/webhook"

print("Testing updated reply options functionality...")
print("=" * 50)

# Test "Get Loan" reply
print("Testing 'Get Loan' reply...")
try:
    response = requests.post(
        webhook_url,
        json=get_loan_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test "Check Eligibility" reply
print("Testing 'Check Eligibility' reply...")
try:
    response = requests.post(
        webhook_url,
        json=check_eligibility_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
print()

# Test "More Details" reply
print("Testing 'More Details' reply...")
try:
    response = requests.post(
        webhook_url,
        json=more_details_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")