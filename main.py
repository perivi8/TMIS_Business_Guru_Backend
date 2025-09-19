import os
from app import app

print("🔄 Importing blueprints...")
try:
    from client_routes import client_bp
    print("✅ client_bp imported successfully")
except Exception as e:
    print(f"❌ Failed to import client_bp: {e}")
    client_bp = None

try:
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
except Exception as e:
    print(f"❌ Failed to import enquiry_bp: {e}")
    enquiry_bp = None

# Register blueprints with URL prefixes
if client_bp:
    app.register_blueprint(client_bp, url_prefix='/api')
    print("✅ client_bp registered with /api prefix")
else:
    print("❌ client_bp not registered - import failed")

if enquiry_bp:
    app.register_blueprint(enquiry_bp, url_prefix='/api')
    print("✅ enquiry_bp registered with /api prefix")
else:
    print("❌ enquiry_bp not registered - import failed")

print(f"📋 Total registered blueprints: {len(app.blueprints)}")
print(f"📋 Blueprint names: {list(app.blueprints.keys())}")


if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
