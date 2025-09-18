import os
from app import app
from client_routes import client_bp
from enquiry_routes import enquiry_bp

# Register blueprints
app.register_blueprint(client_bp)
app.register_blueprint(enquiry_bp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
