#!/usr/bin/env python3
"""
Minimal Flask app for testing Render deployment
This is a stripped-down version to test if the basic setup works
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'tmis-business-guru-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# CORS configuration with enhanced settings
CORS(app, origins=[
    "http://localhost:4200",
    "http://localhost:4201", 
    "https://tmis-business-guru.vercel.app"
], supports_credentials=True,
allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"],
methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# JWT setup
jwt = JWTManager(app)

# Handle preflight OPTIONS requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', "true")
        return response

# Routes
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'TMIS Business Guru Backend is running (minimal version)',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0-minimal'
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'message': 'Test endpoint working',
        'cors': 'enabled',
        'jwt': 'configured'
    }), 200

@app.route('/api/login', methods=['POST'])
def test_login():
    """Test login endpoint that doesn't require database"""
    # Create a test token
    access_token = create_access_token(identity='test@tmis.com')
    return jsonify({
        'access_token': access_token,
        'message': 'Test login successful'
    }), 200

@app.route('/api/clients', methods=['GET'])
@jwt_required()
def test_clients():
    """Test clients endpoint that returns mock data"""
    current_user = get_jwt_identity()
    return jsonify({
        'message': 'Clients endpoint working',
        'user': current_user,
        'clients': [
            {
                'id': '1',
                'legal_name': 'Test Client 1',
                'status': 'pending'
            },
            {
                'id': '2', 
                'legal_name': 'Test Client 2',
                'status': 'interested'
            }
        ]
    }), 200

@app.route('/api/enquiries', methods=['GET'])
@jwt_required()
def test_enquiries():
    """Test enquiries endpoint that returns mock data"""
    current_user = get_jwt_identity()
    return jsonify({
        'message': 'Enquiries endpoint working',
        'user': current_user,
        'enquiries': [
            {
                'id': '1',
                'wati_name': 'Test Enquiry 1',
                'user_name': 'John Doe',
                'mobile_number': '9876543210',
                'gst': 'Yes',
                'gst_status': 'Active',
                'business_type': 'Manufacturing',
                'staff': 'admin@tmis.com',
                'comments': 'Interested in GST registration',
                'date': '2024-01-15'
            },
            {
                'id': '2',
                'wati_name': 'Test Enquiry 2', 
                'user_name': 'Jane Smith',
                'mobile_number': '9876543211',
                'gst': 'No',
                'business_type': 'Service',
                'staff': 'user@tmis.com',
                'comments': 'New business setup',
                'date': '2024-01-16'
            }
        ]
    }), 200

@app.route('/api/enquiries', methods=['POST'])
@jwt_required()
def create_enquiry():
    """Test create enquiry endpoint"""
    current_user = get_jwt_identity()
    data = request.get_json()
    
    # Mock response for enquiry creation
    return jsonify({
        'message': 'Enquiry created successfully (mock)',
        'user': current_user,
        'enquiry': {
            'id': '3',
            'wati_name': data.get('wati_name', 'Test'),
            'user_name': data.get('user_name', 'Test User'),
            'mobile_number': data.get('mobile_number', '0000000000'),
            'gst': data.get('gst', 'No'),
            'business_type': data.get('business_type', 'Other'),
            'staff': current_user,
            'comments': data.get('comments', 'Test enquiry'),
            'date': datetime.utcnow().strftime('%Y-%m-%d')
        }
    }), 201

# Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'msg': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'msg': 'Invalid token'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'msg': 'Authorization token is required'}), 401

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting Minimal TMIS Backend...")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"JWT Secret: {'*' * 10}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
