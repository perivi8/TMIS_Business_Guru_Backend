from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import uuid
import threading
import time

# Store for pending approval requests and admin sessions
pending_approvals = {}
admin_sessions = {}

def init_socketio_handlers(socketio, users_collection):
    """Initialize all SocketIO event handlers"""
    
    @socketio.on('connect')
    def on_connect():
        print(f'Client connected: {socketio.request.sid}')

    @socketio.on('disconnect')
    def on_disconnect():
        print(f'Client disconnected: {socketio.request.sid}')
        # Remove from admin sessions if it was an admin
        if socketio.request.sid in admin_sessions:
            del admin_sessions[socketio.request.sid]

    @socketio.on('admin_login')
    def on_admin_login(data):
        """Register admin session for receiving approval requests"""
        try:
            user_id = data.get('user_id')
            role = data.get('role')
            
            if role == 'admin':
                admin_sessions[socketio.request.sid] = {
                    'user_id': user_id,
                    'connected_at': datetime.utcnow()
                }
                join_room('admins')
                print(f'Admin {user_id} joined approval room: {socketio.request.sid}')
                emit('admin_registered', {'status': 'success'})
        except Exception as e:
            print(f'Error in admin_login: {e}')
            emit('error', {'message': 'Failed to register admin session'})

    @socketio.on('approval_response')
    def on_approval_response(data):
        """Handle admin approval/rejection response"""
        try:
            approval_id = data.get('approval_id')
            action = data.get('action')  # 'approve' or 'reject'
            reason = data.get('reason', '')
            
            if approval_id not in pending_approvals:
                emit('error', {'message': 'Approval request not found'})
                return
            
            approval_request = pending_approvals[approval_id]
            user_data = approval_request['user_data']
            
            if action == 'approve':
                # Save user to database
                user_data['status'] = 'active'
                user_data['approved_at'] = datetime.utcnow()
                user_data['approved_by'] = admin_sessions.get(socketio.request.sid, {}).get('user_id', 'unknown')
                
                result = users_collection.insert_one(user_data)
                
                # Notify the registering user
                socketio.emit('registration_result', {
                    'status': 'approved',
                    'message': 'Registration Verified! Your account has been approved.',
                    'user_id': str(result.inserted_id)
                }, room=approval_request['user_session'])
                
            else:  # reject
                # Notify the registering user
                socketio.emit('registration_result', {
                    'status': 'rejected',
                    'message': f'You are not approved by admin. Reason: {reason}' if reason else 'You are not approved by admin.'
                }, room=approval_request['user_session'])
            
            # Remove from pending approvals
            del pending_approvals[approval_id]
            
            # Confirm to admin
            emit('approval_processed', {
                'approval_id': approval_id,
                'action': action,
                'status': 'success'
            })
            
        except Exception as e:
            print(f'Error in approval_response: {e}')
            emit('error', {'message': 'Failed to process approval response'})

    def cleanup_expired_approvals():
        """Clean up expired approval requests (30+ seconds old)"""
        current_time = datetime.utcnow()
        expired_ids = []
        
        for approval_id, approval_data in pending_approvals.items():
            if (current_time - approval_data['created_at']).total_seconds() > 30:
                expired_ids.append(approval_id)
                
                # Notify user that request expired
                socketio.emit('registration_result', {
                    'status': 'timeout',
                    'message': 'Admin approval timeout. Please try again.',
                    'show_resend': True
                }, room=approval_data['user_session'])
        
        # Remove expired requests
        for approval_id in expired_ids:
            del pending_approvals[approval_id]

    # Run cleanup every 10 seconds
    def start_cleanup_thread():
        def cleanup_loop():
            while True:
                time.sleep(10)
                cleanup_expired_approvals()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    # Start the cleanup thread
    start_cleanup_thread()

def create_approval_request(socketio, user_data, user_session_id):
    """Create a new approval request and notify admins"""
    approval_id = str(uuid.uuid4())
    
    pending_approvals[approval_id] = {
        'user_data': user_data,
        'user_session': user_session_id,
        'created_at': datetime.utcnow()
    }
    
    # Send approval request to all connected admins
    socketio.emit('approval_request', {
        'approval_id': approval_id,
        'username': user_data['username'],
        'email': user_data['email'],
        'message': f"User {user_data['username']} ({user_data['email']}) asked to join as a user in TMIS Business Guru. Do you approve?",
        'created_at': datetime.utcnow().isoformat()
    }, room='admins')
    
    return approval_id
