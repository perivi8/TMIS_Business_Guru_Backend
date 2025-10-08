import os
import sys
from flask import Flask
from werkzeug.test import EnvironBuilder

# Set environment variables to mimic production
os.environ['FLASK_ENV'] = 'production'
os.environ['MONGODB_URI'] = 'mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0'
os.environ['JWT_SECRET_KEY'] = 'tmis-business-guru-secret-key-2024'

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Testing Webhook Endpoint ===")

try:
    # Import app
    from app import app
    
    # Create a test client
    with app.test_client() as client:
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
        
        print("🔄 Sending test request to webhook endpoint...")
        
        # Send POST request to the webhook endpoint
        response = client.post(
            '/api/enquiries/whatsapp/webhook',
            json=webhook_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Data: {response.get_json()}")
        
        if response.status_code == 200:
            print("✅ Webhook endpoint is working correctly!")
        else:
            print("❌ Webhook endpoint returned an error")
            
except Exception as e:
    print(f"❌ Error testing webhook endpoint: {e}")
    import traceback
    traceback.print_exc()