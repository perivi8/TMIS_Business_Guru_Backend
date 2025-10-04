from flask import request, jsonify
from flask_socketio import emit
import bcrypt
from datetime import datetime
from socketio_handlers import create_approval_request

def create_realtime_register_endpoint(app, socketio, db, users_collection):
    """Create the new real-time registration endpoint"""
    
    @app.route('/api/register-realtime', methods=['POST'])
    def register_realtime():
        try:
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirmPassword')
            user_session_id = data.get('session_id')  # Frontend should send this
            
            if not all([username, email, password, confirm_password]):
                return jsonify({'error': 'All fields are required'}), 400
            
            if password != confirm_password:
                return jsonify({'error': 'Passwords do not match'}), 400
            
            # Check database connection
            if db is None:
                return jsonify({'error': 'Database connection failed'}), 500
            
            # Check if user already exists
            existing_user = users_collection.find_one({'email': email})
            if existing_user:
                return jsonify({'error': 'User already exists'}), 400
            
            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Create user data (but don't save to DB yet)
            user_data = {
                'username': username,
                'email': email,
                'password': hashed_password,
                'role': 'user',
                'created_at': datetime.utcnow()
            }
            
            # Create approval request and notify admins
            approval_id = create_approval_request(socketio, user_data, user_session_id)
            
            return jsonify({
                'message': 'Approval request sent to admin. Please wait...',
                'approval_id': approval_id,
                'status': 'pending_approval'
            }), 200
            
        except Exception as e:
            print(f"Registration error: {e}")
            return jsonify({'error': str(e)}), 500
    
    return register_realtime
