import os
from app import app
from client_routes import client_bp
from enquiry_routes import enquiry_bp

# Register blueprints
app.register_blueprint(client_bp)
app.register_blueprint(enquiry_bp)

if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
