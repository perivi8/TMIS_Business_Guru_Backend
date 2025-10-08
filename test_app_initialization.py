import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Create app similar to app.py
app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'test-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
jwt = JWTManager(app)

# CORS Configuration
cors = CORS()
cors.init_app(app, origins=["*"])

print("=== Testing Blueprint Registration ===")

# Test blueprint registration
try:
    print("🔄 Importing enquiry blueprint...")
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
    
    # Register blueprint
    app.register_blueprint(enquiry_bp, url_prefix='/api')
    print("✅ Enquiry blueprint registered successfully")
    
    # Test direct route registration
    print("🔄 Testing direct route registration...")
    from enquiry_routes import handle_incoming_whatsapp
    app.add_url_rule('/api/enquiries/whatsapp/webhook', 'handle_incoming_whatsapp', handle_incoming_whatsapp, methods=['POST'])
    print("✅ Webhook route registered directly")
    
    # Check registered routes
    print("\n=== Registered Routes ===")
    webhook_found = False
    for rule in app.url_map.iter_rules():
        rule_str = str(rule)
        if '/webhook' in rule_str:
            print(f"✅ Webhook route found: {rule_str}")
            webhook_found = True
        elif '/api/enquiries' in rule_str:
            print(f"🔍 Enquiry route: {rule_str}")
    
    if not webhook_found:
        print("❌ Webhook route NOT found in url_map")
        
    # List all routes with 'webhook' in the name
    print("\n=== All Webhook Routes ===")
    for rule in app.url_map.iter_rules():
        if 'webhook' in str(rule).lower():
            print(f"  {rule}")
            
    # List all API routes
    print("\n=== All API Routes ===")
    api_routes = [str(rule) for rule in app.url_map.iter_rules() if str(rule).startswith('/api/')]
    for route in sorted(api_routes):
        print(f"  {route}")
        
except Exception as e:
    print(f"❌ Error during blueprint registration: {e}")
    import traceback
    traceback.print_exc()