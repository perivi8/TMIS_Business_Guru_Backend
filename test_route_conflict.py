import os
import sys

# Set environment variables to mimic production
os.environ['FLASK_ENV'] = 'production'
os.environ['MONGODB_URI'] = 'mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0'
os.environ['JWT_SECRET_KEY'] = 'tmis-business-guru-secret-key-2024'

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Testing Route Conflict ===")

try:
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
    
    # Test blueprint registration only
    print("🔄 Testing blueprint registration only...")
    from enquiry_routes import enquiry_bp
    app.register_blueprint(enquiry_bp, url_prefix='/api')
    print("✅ Enquiry blueprint registered successfully")
    
    # Check webhook route
    webhook_routes = []
    for rule in app.url_map.iter_rules():
        if '/api/enquiries/whatsapp/webhook' in str(rule):
            webhook_routes.append((str(rule), rule.endpoint))
    
    print(f"Webhook routes after blueprint registration: {webhook_routes}")
    
    # Test direct route registration only
    print("\n🔄 Testing direct route registration only...")
    # Create a new app for this test
    app2 = Flask(__name__)
    cors2 = CORS()
    cors2.init_app(app2, origins=["*"])
    app2.config['JWT_SECRET_KEY'] = 'test-secret-key'
    jwt2 = JWTManager(app2)
    
    from enquiry_routes import handle_incoming_whatsapp
    app2.add_url_rule('/api/enquiries/whatsapp/webhook', 'handle_incoming_whatsapp', handle_incoming_whatsapp, methods=['POST'])
    print("✅ Webhook route registered directly")
    
    # Check webhook route
    webhook_routes2 = []
    for rule in app2.url_map.iter_rules():
        if '/api/enquiries/whatsapp/webhook' in str(rule):
            webhook_routes2.append((str(rule), rule.endpoint))
    
    print(f"Webhook routes after direct registration: {webhook_routes2}")
    
    # Test both together
    print("\n🔄 Testing both registrations together...")
    # Create a new app for this test
    app3 = Flask(__name__)
    cors3 = CORS()
    cors3.init_app(app3, origins=["*"])
    app3.config['JWT_SECRET_KEY'] = 'test-secret-key'
    jwt3 = JWTManager(app3)
    
    # Register blueprint
    from enquiry_routes import enquiry_bp as enquiry_bp3
    app3.register_blueprint(enquiry_bp3, url_prefix='/api')
    print("✅ Enquiry blueprint registered successfully")
    
    # Register direct route
    from enquiry_routes import handle_incoming_whatsapp as handle_incoming_whatsapp3
    app3.add_url_rule('/api/enquiries/whatsapp/webhook', 'handle_incoming_whatsapp', handle_incoming_whatsapp3, methods=['POST'])
    print("✅ Webhook route registered directly")
    
    # Check webhook routes
    webhook_routes3 = []
    for rule in app3.url_map.iter_rules():
        if '/api/enquiries/whatsapp/webhook' in str(rule):
            webhook_routes3.append((str(rule), rule.endpoint))
    
    print(f"Webhook routes after both registrations: {webhook_routes3}")
    
except Exception as e:
    print(f"❌ Error during route conflict test: {e}")
    import traceback
    traceback.print_exc()