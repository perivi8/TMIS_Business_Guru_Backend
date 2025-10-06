import os
import sys
import traceback
from datetime import datetime
from flask import jsonify
from app import app

print("🔄 Importing blueprints...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Force import client_routes with better error handling and database fallback
client_bp = None
try:
    print("🔄 Attempting to import client_routes...")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if client_routes.py exists
    if os.path.exists('client_routes.py'):
        print("✅ client_routes.py file found")
    else:
        print("❌ client_routes.py file not found")
        
    from client_routes import client_bp
    print("✅ client_bp imported successfully")
    print(f"Client blueprint name: {client_bp.name}")
    print(f"Client blueprint url_prefix: {getattr(client_bp, 'url_prefix', 'None')}")
    
except Exception as e:
    print(f"❌ Error importing client_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Create a working fallback client blueprint with database access
    try:
        from flask import Blueprint, jsonify
        from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
        
        print("🔄 Creating enhanced fallback client blueprint...")
        client_bp = Blueprint('client_fallback', __name__)
        
        @client_bp.route('/clients', methods=['GET'])
        @jwt_required()
        def get_clients_fallback():
            try:
                # Try to get database connection from app
                from app import db, clients_collection
                
                if db is None or clients_collection is None:
                    return jsonify({
                        'error': 'Database connection not available',
                        'clients': [],
                        'fallback': True,
                        'message': 'MongoDB connection failed - check environment variables'
                    }), 500
                
                # Get current user info
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                user_role = claims.get('role', 'user')
                
                print(f"Fallback route: User {current_user_id} with role {user_role} requesting clients")
                
                # Get clients from database
                try:
                    if user_role == 'admin':
                        # Admin can see all clients
                        clients_cursor = clients_collection.find()
                    else:
                        # Regular users see only their clients
                        clients_cursor = clients_collection.find({'created_by': current_user_id})
                    
                    clients_list = []
                    for client in clients_cursor:
                        # Convert ObjectId to string
                        client['_id'] = str(client['_id'])
                        clients_list.append(client)
                    
                    print(f"Fallback route: Found {len(clients_list)} clients for user {current_user_id}")
                    
                    return jsonify({
                        'clients': clients_list,
                        'fallback': True,
                        'message': 'Using fallback route - blueprint import failed',
                        'count': len(clients_list)
                    }), 200
                    
                except Exception as db_error:
                    print(f"Database query error: {db_error}")
                    return jsonify({
                        'error': f'Database query failed: {str(db_error)}',
                        'clients': [],
                        'fallback': True,
                        'message': 'Database connection exists but query failed'
                    }), 500
                    
            except Exception as fallback_error:
                print(f"Fallback route error: {fallback_error}")
                return jsonify({
                    'error': f'Fallback route failed: {str(fallback_error)}',
                    'clients': [],
                    'fallback': True,
                    'message': 'Complete system failure'
                }), 500
        
        @client_bp.route('/clients/test', methods=['GET'])
        def test_clients_fallback():
            return jsonify({
                'status': 'fallback_success',
                'message': 'Client routes fallback is working',
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Original client_routes.py failed to import'
            }), 200
        
        print("✅ Enhanced fallback client blueprint created with database access")
    except Exception as fallback_error:
        print(f"❌ Failed to create fallback blueprint: {fallback_error}")
        client_bp = None

# Force import enquiry_routes with better error handling
enquiry_bp = None
try:
    print("🔄 Attempting to import enquiry_routes...")
    
    # Check if enquiry_routes.py exists
    if os.path.exists('enquiry_routes.py'):
        print("✅ enquiry_routes.py file found")
    else:
        print("❌ enquiry_routes.py file not found")
        
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
    print(f"Enquiry blueprint name: {enquiry_bp.name}")
    print(f"Enquiry blueprint url_prefix: {getattr(enquiry_bp, 'url_prefix', 'None')}")
    
except Exception as e:
    print(f"❌ Error importing enquiry_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Create a working fallback enquiry blueprint with database access
    try:
        from flask import Blueprint, jsonify
        from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
        
        print("🔄 Creating enhanced fallback enquiry blueprint...")
        enquiry_bp = Blueprint('enquiry_fallback', __name__)
        
        @enquiry_bp.route('/enquiries', methods=['GET'])
        @jwt_required()
        def get_enquiries_fallback():
            try:
                # Try to get database connection from app
                from app import db
                
                if db is None:
                    return jsonify({
                        'error': 'Database connection not available',
                        'enquiries': [],
                        'fallback': True,
                        'message': 'MongoDB connection failed - check environment variables'
                    }), 500
                
                # Get current user info
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                user_role = claims.get('role', 'user')
                
                print(f"Fallback enquiry route: User {current_user_id} with role {user_role} requesting enquiries")
                
                # Get enquiries from database
                try:
                    enquiries_collection = db.enquiries
                    
                    if user_role == 'admin':
                        # Admin can see all enquiries
                        enquiries_cursor = enquiries_collection.find()
                    else:
                        # Regular users see only their enquiries
                        enquiries_cursor = enquiries_collection.find({'created_by': current_user_id})
                    
                    enquiries_list = []
                    for enquiry in enquiries_cursor:
                        # Convert ObjectId to string
                        enquiry['_id'] = str(enquiry['_id'])
                        enquiries_list.append(enquiry)
                    
                    print(f"Fallback enquiry route: Found {len(enquiries_list)} enquiries for user {current_user_id}")
                    
                    return jsonify({
                        'enquiries': enquiries_list,
                        'fallback': True,
                        'message': 'Using fallback route - blueprint import failed',
                        'count': len(enquiries_list)
                    }), 200
                    
                except Exception as db_error:
                    print(f"Enquiry database query error: {db_error}")
                    return jsonify({
                        'error': f'Database query failed: {str(db_error)}',
                        'enquiries': [],
                        'fallback': True,
                        'message': 'Database connection exists but query failed'
                    }), 500
                    
            except Exception as fallback_error:
                print(f"Enquiry fallback route error: {fallback_error}")
                return jsonify({
                    'error': f'Fallback route failed: {str(fallback_error)}',
                    'enquiries': [],
                    'fallback': True,
                    'message': 'Complete system failure'
                }), 500
        
        @enquiry_bp.route('/enquiries/test', methods=['GET'])
        def test_enquiries_fallback():
            return jsonify({
                'status': 'fallback_success',
                'message': 'Enquiry routes fallback is working',
                'timestamp': datetime.utcnow().isoformat(),
                'note': 'Original enquiry_routes.py failed to import'
            }), 200
        
        print("✅ Enhanced fallback enquiry blueprint created with database access")
    except Exception as fallback_error:
        print(f"❌ Failed to create fallback enquiry blueprint: {fallback_error}")
        enquiry_bp = None

# Check blueprint registration status (blueprints are registered in app.py)
if client_bp:
    if 'client' in app.blueprints:
        print("✅ client_bp already registered in app.py")
    else:
        print("ℹ️ client_bp imported but not registered - this shouldn't happen")
else:
    print("❌ client_bp not available - check client_routes.py import")

if enquiry_bp:
    if 'enquiry' in app.blueprints:
        print("✅ enquiry_bp already registered in app.py")
    else:
        print("ℹ️ enquiry_bp imported but not registered - this shouldn't happen")
else:
    print("❌ enquiry_bp not available - check enquiry_routes.py import")

print(f"📋 Total registered blueprints: {len(app.blueprints)}")
print(f"📋 Blueprint names: {list(app.blueprints.keys())}")

# Comprehensive route verification
print("🔍 Verifying route registration...")
api_routes_found = []
for rule in app.url_map.iter_rules():
    rule_str = str(rule)
    if rule_str.startswith('/api/'):
        api_routes_found.append(f"{rule_str} -> {rule.endpoint} ({list(rule.methods or [])})")
        print(f"✅ Found API route: {rule_str} -> {rule.endpoint} ({list(rule.methods or [])})")

if not api_routes_found:
    print("❌ WARNING: No /api/ routes found!")
else:
    print(f"✅ Total API routes registered: {len(api_routes_found)}")

# Specific check for critical endpoints
critical_endpoints = ['/api/clients', '/api/enquiries', '/api/health', '/api/test-routes']
for endpoint in critical_endpoints:
    found = any(endpoint in route for route in api_routes_found)
    status = "✅" if found else "❌"
    print(f"{status} Critical endpoint {endpoint}: {'FOUND' if found else 'MISSING'}")

# Note: All routes are now properly handled by blueprints registered in app.py
# No additional route registration needed here

if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    # Import socketio and run with SocketIO support
    from app import socketio
    if os.environ.get('FLASK_ENV') == 'production':
        socketio.run(app, host='0.0.0.0', port=port, debug=False, log_output=False)
    else:
        socketio.run(app, host='0.0.0.0', port=port, debug=debug)
