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

# Force import client_routes with better error handling
client_bp = None
try:
    print("🔄 Attempting to import client_routes...")
    from client_routes import client_bp
    print("✅ client_bp imported successfully")
except ImportError as e:
    print(f"❌ ImportError in client_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Try to create a minimal client blueprint as fallback
    try:
        from flask import Blueprint, jsonify
        from flask_jwt_extended import jwt_required
        
        print("🔄 Creating fallback client blueprint...")
        client_bp = Blueprint('client', __name__)
        
        @client_bp.route('/clients', methods=['GET'])
        @jwt_required()
        def get_clients_fallback():
            return jsonify({
                'error': 'Client routes module failed to import properly',
                'clients': [],
                'fallback': True
            }), 500
        
        print("✅ Fallback client blueprint created")
    except Exception as fallback_error:
        print(f"❌ Failed to create fallback blueprint: {fallback_error}")
        client_bp = None
        
except Exception as e:
    print(f"❌ Unexpected error importing client_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    client_bp = None

# Force import enquiry_routes with better error handling
enquiry_bp = None
try:
    print("🔄 Attempting to import enquiry_routes...")
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
except ImportError as e:
    print(f"❌ ImportError in enquiry_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    
    # Try to create a minimal enquiry blueprint as fallback
    try:
        from flask import Blueprint, jsonify
        from flask_jwt_extended import jwt_required
        
        print("🔄 Creating fallback enquiry blueprint...")
        enquiry_bp = Blueprint('enquiry', __name__)
        
        @enquiry_bp.route('/enquiries', methods=['GET'])
        @jwt_required()
        def get_enquiries_fallback():
            return jsonify({
                'error': 'Enquiry routes module failed to import properly',
                'enquiries': [],
                'fallback': True
            }), 500
        
        print("✅ Fallback enquiry blueprint created")
    except Exception as fallback_error:
        print(f"❌ Failed to create fallback enquiry blueprint: {fallback_error}")
        enquiry_bp = None
        
except Exception as e:
    print(f"❌ Unexpected error importing enquiry_routes: {e}")
    print(f"Traceback: {traceback.format_exc()}")
    enquiry_bp = None

# Register blueprints with URL prefixes - ALWAYS try to register something
if client_bp:
    try:
        app.register_blueprint(client_bp, url_prefix='/api')
        print("✅ client_bp registered with /api prefix")
    except Exception as e:
        print(f"❌ Failed to register client_bp: {e}")
        print(f"Traceback: {traceback.format_exc()}")
else:
    print("❌ client_bp not available - creating emergency fallback")
    # Create emergency fallback route directly on app
    @app.route('/api/clients', methods=['GET'])
    def emergency_clients():
        try:
            # Try to import and use the database connection from app.py
            from app import db, clients_collection
            
            if db is None or clients_collection is None:
                return jsonify({
                    'error': 'Database connection not available',
                    'clients': [],
                    'emergency_fallback': True,
                    'message': 'MongoDB connection failed - check environment variables'
                }), 500
            
            # Try to get clients from database
            try:
                clients_cursor = clients_collection.find()
                clients_list = []
                
                for client in clients_cursor:
                    # Convert ObjectId to string
                    client['_id'] = str(client['_id'])
                    clients_list.append(client)
                
                return jsonify({
                    'clients': clients_list,
                    'emergency_fallback': True,
                    'message': 'Emergency fallback route working - blueprint import failed',
                    'count': len(clients_list)
                }), 200
                
            except Exception as db_error:
                return jsonify({
                    'error': f'Database query failed: {str(db_error)}',
                    'clients': [],
                    'emergency_fallback': True,
                    'message': 'Database connection exists but query failed'
                }), 500
                
        except ImportError:
            return jsonify({
                'error': 'Cannot import database connection from app.py',
                'clients': [],
                'emergency_fallback': True,
                'message': 'Complete database connection failure'
            }), 500
        except Exception as e:
            return jsonify({
                'error': f'Emergency fallback failed: {str(e)}',
                'clients': [],
                'emergency_fallback': True,
                'message': 'Critical system error'
            }), 500

if enquiry_bp:
    try:
        app.register_blueprint(enquiry_bp, url_prefix='/api')
        print("✅ enquiry_bp registered with /api prefix")
    except Exception as e:
        print(f"❌ Failed to register enquiry_bp: {e}")
        print(f"Traceback: {traceback.format_exc()}")
else:
    print("❌ enquiry_bp not available - creating emergency fallback")
    # Create emergency fallback route directly on app
    @app.route('/api/enquiries', methods=['GET'])
    def emergency_enquiries():
        return jsonify({
            'error': 'Enquiry blueprint registration failed',
            'enquiries': [],
            'emergency_fallback': True,
            'message': 'Please check server logs for import errors'
        }), 500

print(f"📋 Total registered blueprints: {len(app.blueprints)}")
print(f"📋 Blueprint names: {list(app.blueprints.keys())}")

# Comprehensive route verification
print("🔍 Verifying route registration...")
api_routes_found = []
for rule in app.url_map.iter_rules():
    rule_str = str(rule)
    if rule_str.startswith('/api/'):
        api_routes_found.append(f"{rule_str} -> {rule.endpoint} ({list(rule.methods)})")
        print(f"✅ Found API route: {rule_str} -> {rule.endpoint} ({list(rule.methods)})")

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

# Add comprehensive test route for debugging
@app.route('/api/test-routes', methods=['GET'])
def test_routes():
    """Comprehensive route testing endpoint"""
    try:
        from flask import current_app
        
        routes_info = []
        for rule in current_app.url_map.iter_rules():
            routes_info.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': str(rule)
            })
        
        # Test database connections
        db_status = "Unknown"
        try:
            if 'client_routes' in sys.modules:
                from client_routes import db, clients_collection
                if db and clients_collection:
                    db.command("ping")
                    client_count = clients_collection.count_documents({})
                    db_status = f"Connected - {client_count} clients"
                else:
                    db_status = "Database objects not available"
            else:
                db_status = "client_routes module not imported"
        except Exception as e:
            db_status = f"Database error: {str(e)}"
        
        # Check blueprint status
        blueprint_status = {}
        for bp_name in app.blueprints:
            blueprint_status[bp_name] = "Registered"
        
        return jsonify({
            'status': 'success',
            'message': 'Route testing endpoint working',
            'total_routes': len(routes_info),
            'api_routes': [r for r in routes_info if r['rule'].startswith('/api/')],
            'blueprint_status': blueprint_status,
            'database_status': db_status,
            'critical_endpoints': {
                '/api/clients': any('/api/clients' in r['rule'] for r in routes_info),
                '/api/enquiries': any('/api/enquiries' in r['rule'] for r in routes_info),
                '/api/login': any('/api/login' in r['rule'] for r in routes_info),
                '/api/register': any('/api/register' in r['rule'] for r in routes_info)
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Route testing failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Add a simple clients test endpoint that doesn't require JWT
@app.route('/api/clients/test', methods=['GET'])
def test_clients_endpoint():
    """Test clients endpoint without authentication"""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Clients test endpoint is working',
            'endpoint': '/api/clients/test',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'This confirms the /api/clients route structure is accessible'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Clients test endpoint failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

if __name__ == '__main__':
    # Use environment variables for production deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Port: {port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    app.run(debug=debug, host='0.0.0.0', port=port)
