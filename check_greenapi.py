import os
import requests
from dotenv import load_dotenv

load_dotenv()

instance_id = os.getenv('GREENAPI_INSTANCE_ID')
token = os.getenv('GREENAPI_TOKEN')

print(f"Instance ID: {instance_id}")

# Check settings
response = requests.get(f'https://api.green-api.com/waInstance{instance_id}/getSettings/{token}')
if response.status_code == 200:
    settings = response.json()
    print(f"Webhook URL: {settings.get('webhookUrl', 'Not set')}")
    print(f"Incoming Webhook: {settings.get('incomingWebhook', 'Not set')}")
    print(f"Outgoing Webhook: {settings.get('outgoingWebhook', 'Not set')}")
    print(f"State Webhook: {settings.get('stateWebhook', 'Not set')}")
else:
    print(f"Error: {response.status_code} - {response.text}")
