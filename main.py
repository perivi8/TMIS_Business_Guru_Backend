import os
import logging
from app import app
from client_routes import client_bp
from enquiry_routes import enquiry_bp

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(client_bp)
app.register_blueprint(enquiry_bp)

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return {'status': 'healthy', 'message': 'TMIS Business Guru Backend is running'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting TMIS Business Guru Backend on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
