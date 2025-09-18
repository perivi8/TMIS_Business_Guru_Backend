import os
import logging
import sys
from flask import Flask, jsonify

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create a fallback Flask app in case main app fails to import
fallback_app = Flask(__name__)

try:
    from app import app
    logger.info("Successfully imported app")
    
    # Import blueprints with individual error handling
    try:
        from client_routes import client_bp
        app.register_blueprint(client_bp)
        logger.info("Successfully imported and registered client_routes")
    except Exception as e:
        logger.error(f"Failed to import client_routes: {str(e)}")
        # Continue without client routes for basic functionality
    
    try:
        from enquiry_routes import enquiry_bp
        app.register_blueprint(enquiry_bp)
        logger.info("Successfully imported and registered enquiry_routes")
    except Exception as e:
        logger.error(f"Failed to import enquiry_routes: {str(e)}")
        # Continue without enquiry routes for basic functionality
    
    logger.info("Application initialization completed")
    
except Exception as e:
    logger.error(f"Critical failure during app initialization: {str(e)}")
    # Use fallback app for basic functionality
    app = fallback_app
    logger.info("Using fallback Flask app")

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    try:
        # Check environment variables
        mongodb_uri = os.getenv('MONGODB_URI')
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        
        status = {
            'status': 'healthy',
            'message': 'TMIS Business Guru Backend is running',
            'mongodb_configured': bool(mongodb_uri),
            'jwt_configured': bool(jwt_secret),
            'port': os.environ.get('PORT', '5000')
        }
        
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Add health check to fallback app as well
@fallback_app.route('/health')
def fallback_health_check():
    """Fallback health check endpoint"""
    return jsonify({
        'status': 'limited',
        'message': 'TMIS Backend running in fallback mode',
        'port': os.environ.get('PORT', '5000')
    }), 200

@app.route('/debug/env')
def debug_env():
    """Debug endpoint to check environment variables (remove in production)"""
    try:
        env_vars = {
            'MONGODB_URI': 'SET' if os.getenv('MONGODB_URI') else 'NOT SET',
            'JWT_SECRET_KEY': 'SET' if os.getenv('JWT_SECRET_KEY') else 'NOT SET',
            'EMAIL_HOST': os.getenv('EMAIL_HOST', 'NOT SET'),
            'EMAIL_PORT': os.getenv('EMAIL_PORT', 'NOT SET'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'NOT SET'),
            'PORT': os.getenv('PORT', 'NOT SET')
        }
        return jsonify(env_vars), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'Please check server logs for details'
    }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting TMIS Business Guru Backend on port {port}")
        logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        app.run(debug=False, host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)
