import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a minimal Flask app to test route registration
from flask import Flask

app = Flask(__name__)

try:
    # Try to import the function
    from enquiry_routes import handle_incoming_whatsapp
    print("✅ Successfully imported handle_incoming_whatsapp")
    
    # Try to register the route directly
    app.add_url_rule('/api/enquiries/whatsapp/webhook', 'handle_incoming_whatsapp', handle_incoming_whatsapp, methods=['POST'])
    print("✅ Route registered successfully")
    
    # Check if the route is in the app's url map
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(str(rule))
    
    if '/api/enquiries/whatsapp/webhook' in routes:
        print("✅ Route found in url_map")
    else:
        print("❌ Route NOT found in url_map")
        print("Available routes:")
        for route in sorted(routes):
            print(f"  {route}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()