import os
import sys
import traceback
from app import app

print("🔄 Importing blueprints...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from client_routes import client_bp
    print("✅ client_bp imported successfully")
except Exception as e:
    print(f"❌ Failed to import client_bp: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    client_bp = None

try:
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
except Exception as e:
    print(f"❌ Failed to import enquiry_bp: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    enquiry_bp = None

# Register blueprints with URL prefixes
if client_bp:
    try:
        app.register_blueprint(client_bp, url_prefix='/api')
        print("✅ client_bp registered with /api prefix")
    except Exception as e:
        print(f"❌ Failed to register client_bp: {e}")
        print(f"Traceback: {traceback.format_exc()}")
else:
    print("❌ client_bp not registered - import failed")

if enquiry_bp:
    try:
        app.register_blueprint(enquiry_bp, url_prefix='/api')
        print("✅ enquiry_bp registered with /api prefix")
    except Exception as e:
        print(f"❌ Failed to register enquiry_bp: {e}")
        print(f"Traceback: {traceback.format_exc()}")
else:
    print("❌ enquiry_bp not registered - import failed")

print(f"📋 Total registered blueprints: {len(app.blueprints)}")
print(f"📋 Blueprint names: {list(app.blueprints.keys())}")

# Additional check to verify route registration
print("🔍 Verifying route registration...")
for rule in app.url_map.iter_rules():
    if str(rule).startswith('/api/clients'):
        print(f"✅ Found route: {rule} (endpoint: {rule.endpoint})")

if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
