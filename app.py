from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
import sys
from dotenv import load_dotenv
import smtplib
from datetime import datetime, timedelta
import PyPDF2
import json
import re
from pymongo import MongoClient
from bson import ObjectId
from bson.json_util import dumps
import bcrypt

# Load environment variables
load_dotenv()

app = Flask(__name__)

# JWT Configuration with consistent secret key
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'tmis-business-guru-secret-key-2024')
app.config['JWT_SECRET_KEY'] = JWT_SECRET
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'  # Explicitly set algorithm
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

print(f"=== JWT CONFIGURATION ===")
print(f"JWT Secret Key: {JWT_SECRET}")
print(f"JWT Algorithm: {app.config['JWT_ALGORITHM']}")
print(f"JWT Expires: {app.config['JWT_ACCESS_TOKEN_EXPIRES']}")

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize CORS with default settings
cors = CORS()

# Configure CORS
# Get allowed origins from environment or use defaults
allowed_origins = [
    "http://localhost:4200", 
    "http://localhost:4201", 
    "https://tmis-business-guru.vercel.app",
    "https://tmis-business-guru-frontend.vercel.app"
]

# Add any additional origins from environment variable
additional_origins = os.getenv('ADDITIONAL_CORS_ORIGINS', '')
if additional_origins:
    allowed_origins.extend(additional_origins.split(','))

# For production, add comprehensive Vercel domain patterns
flask_env = os.getenv('FLASK_ENV', 'development')
if flask_env == 'production':
    # Add all possible Vercel domain patterns based on your project
    vercel_domains = [
        "https://tmis-business-guru-git-main-perivihks-projects.vercel.app",
        "https://tmis-business-guru-perivihks-projects.vercel.app",
        "https://tmis-business-guru-git-main.vercel.app",
        "https://tmis-business-guru-frontend.vercel.app",
        "https://tmis-business-guru-frontend-git-main.vercel.app",
        "https://tmis-business-guru-frontend-perivihks-projects.vercel.app",
        # Add common Vercel patterns for your username
        "https://tmis-business-guru-perivihk.vercel.app",
        "https://tmis-business-guru-git-main-perivihk.vercel.app",
        # Add more comprehensive patterns for Angular deployment
        "https://tmis-business-guru-frontend-git-main-perivihks-projects.vercel.app",
        "https://tmis-business-guru-angular.vercel.app",
        "https://tmis-business-guru-angular-git-main.vercel.app",
        "https://tmis-business-guru-angular-perivihks-projects.vercel.app",
        # Add wildcard patterns for any Vercel subdomain
        "https://*.vercel.app"
    ]
    allowed_origins.extend(vercel_domains)
    print(f"🔧 Production mode: Added Vercel domains to CORS")

print(f"🌐 CORS Allowed Origins: {allowed_origins}")
print(f"🔧 Flask Environment: {flask_env}")

# Configure CORS with comprehensive settings
cors.init_app(
    app,
    resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            "allow_headers": [
                "Content-Type", 
                "Authorization", 
                "X-Requested-With",
                "Accept",
                "Origin",
                "Cache-Control",
                "X-Forwarded-For",
                "X-Real-IP"
            ],
            "supports_credentials": True,
            "expose_headers": [
                "Content-Disposition",
                "Authorization",
                "Access-Control-Allow-Origin"
            ],
            "send_wildcard": False,
            "always_send": True,
            "automatic_options": True,
            "max_age": 86400  # Cache preflight for 24 hours
        }
    }
)
jwt = JWTManager(app)

# Health check endpoint (no JWT required)
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'TMIS Business Guru Backend is running',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'API is running',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/status', methods=['GET'])
def comprehensive_status():
    """Comprehensive status endpoint for debugging"""
    try:
        # Test database connection
        db_status = "Unknown"
        db_details = {}
        
        if db is not None:
            try:
                db.command("ping")
                user_count = users_collection.count_documents({}) if users_collection else 0
                client_count = clients_collection.count_documents({}) if clients_collection else 0
                db_status = "Connected"
                db_details = {
                    "users": user_count,
                    "clients": client_count,
                    "database_name": db.name
                }
            except Exception as db_error:
                db_status = f"Error: {str(db_error)}"
        else:
            db_status = "Not connected"
        
        # Check environment variables
        env_vars = {
            "MONGODB_URI": "Set" if os.getenv('MONGODB_URI') else "Missing",
            "JWT_SECRET_KEY": "Set" if os.getenv('JWT_SECRET_KEY') else "Missing",
            "FLASK_ENV": os.getenv('FLASK_ENV', 'Not set'),
            "SMTP_EMAIL": "Set" if os.getenv('SMTP_EMAIL') else "Missing",
            "UPLOAD_FOLDER": os.getenv('UPLOAD_FOLDER', 'Not set')
        }
        
        return jsonify({
            'status': 'healthy',
            'message': 'Comprehensive status check',
            'timestamp': datetime.utcnow().isoformat(),
            'database': {
                'status': db_status,
                'details': db_details
            },
            'environment': env_vars,
            'flask': {
                'debug': app.debug,
                'testing': app.testing,
                'secret_key_set': bool(app.config.get('JWT_SECRET_KEY'))
            },
            'system': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'working_directory': os.getcwd()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Status check failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/api/cors-debug', methods=['GET', 'OPTIONS'])
def cors_debug():
    """Debug endpoint to check CORS configuration"""
    origin = request.headers.get('Origin', 'No Origin Header')
    
    return jsonify({
        'message': 'CORS Debug Endpoint',
        'request_origin': origin,
        'allowed_origins': allowed_origins,
        'request_headers': dict(request.headers),
        'cors_configured': True,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/validate-token', methods=['GET'])
@jwt_required()
def validate_token():
    """Endpoint to validate JWT token and return user info"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        print(f"=== TOKEN VALIDATION ===")
        print(f"User ID: {current_user_id}")
        print(f"Claims: {claims}")
        
        return jsonify({
            'valid': True,
            'user_id': current_user_id,
            'claims': claims,
            'message': 'Token is valid',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Token validation error: {e}")
        return jsonify({
            'valid': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 401

# Handle preflight OPTIONS requests and log protected endpoints
@app.before_request
def handle_requests():
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        # Let Flask-CORS handle the OPTIONS request
        # Don't add any manual headers here as it causes duplicates
        return '', 200
    
    # Log protected endpoint requests for debugging
    if request.endpoint and any(protected in request.path for protected in ['/api/team', '/api/clients']):
        print(f"=== PROTECTED ENDPOINT REQUEST ===")
        print(f"Path: {request.path}")
        print(f"Method: {request.method}")
        print(f"Authorization header: {request.headers.get('Authorization', 'Missing')}")
        print(f"Origin: {request.headers.get('Origin', 'No origin')}")
        print(f"User-Agent: {request.headers.get('User-Agent', 'No user agent')}")
        
        # Check if token is present and valid format
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            print(f"Token present: {token[:20]}...{token[-10:] if len(token) > 30 else token}")
        else:
            print("No Bearer token found in Authorization header")

# JWT Error Handlers with enhanced debugging
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("=== JWT TOKEN EXPIRED ===")
    print(f"Header: {jwt_header}")
    print(f"Payload: {jwt_payload}")
    print(f"Expired at: {jwt_payload.get('exp', 'Unknown')}")
    return jsonify({
        'msg': 'Token has expired', 
        'error': 'expired_token',
        'timestamp': datetime.utcnow().isoformat()
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"=== JWT INVALID TOKEN ===")
    print(f"Error: {error}")
    print(f"Request headers: {dict(request.headers)}")
    return jsonify({
        'msg': 'Invalid token format or signature', 
        'error': 'invalid_token',
        'details': str(error)
    }), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"=== JWT MISSING TOKEN ===")
    print(f"Error: {error}")
    print(f"Authorization header: {request.headers.get('Authorization', 'Not present')}")
    print(f"All headers: {dict(request.headers)}")
    return jsonify({
        'msg': 'Authorization token is required', 
        'error': 'missing_token',
        'hint': 'Include Authorization: Bearer <token> in request headers'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    print("=== JWT TOKEN REVOKED ===")
    print(f"Header: {jwt_header}")
    print(f"Payload: {jwt_payload}")
    return jsonify({
        'msg': 'Token has been revoked', 
        'error': 'revoked_token'
    }), 401

# Add JWT token validation debugging
@jwt.additional_claims_loader
def add_claims_to_jwt(identity):
    return {'iat': datetime.utcnow().timestamp()}


# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    print("❌ CRITICAL ERROR: MONGODB_URI environment variable not found!")
    print("Please set MONGODB_URI in your Render dashboard environment variables")
    print("Required format: mongodb+srv://username:password@cluster.mongodb.net/database_name?retryWrites=true&w=majority")
    raise ValueError("MONGODB_URI environment variable is required for production deployment")

print(f"🔄 Connecting to MongoDB...")
print(f"MongoDB URI: {MONGODB_URI[:50]}...{MONGODB_URI[-20:]}")  # Hide credentials in logs

try:
    client = MongoClient(MONGODB_URI)
    db = client.tmis_business_guru
    # Test connection
    db.command("ping")
    print("✅ MongoDB connection successful")
    
    # Initialize collections
    users_collection = db.users
    clients_collection = db.clients
    
    # Test collections access
    try:
        user_count = users_collection.count_documents({})
        client_count = clients_collection.count_documents({})
        print(f"📊 Database stats: {user_count} users, {client_count} clients")
    except Exception as stats_error:
        print(f"⚠️ Warning: Could not get collection stats: {stats_error}")
        
except Exception as e:
    print(f"❌ MongoDB connection failed: {str(e)}")
    print("🔍 Troubleshooting:")
    print("1. Check if MongoDB URI includes database name")
    print("2. Verify MongoDB Atlas cluster is running")
    print("3. Check network connectivity and IP whitelist")
    print("4. Verify credentials in MongoDB URI")
    print("🔧 Setting database objects to None - app will use fallback behavior")
    
    # Don't raise exception, just set to None for graceful degradation
    db = None
    users_collection = None
    clients_collection = None

# Collections are already initialized in the try/except block above
# This section is kept for compatibility but collections are already set

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(to_email, subject, body):
    """Send email notification"""
    try:
        import email.mime.text
        import email.mime.multipart
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = email.mime.multipart.MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(email.mime.text.MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        
        if not all([username, email, password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'User already exists'}), 400
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': 'user',  # Default role
            'created_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_data)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        print(f"=== LOGIN DEBUG ===")
        print(f"Login attempt for email: {email}")
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check database connection
        if db is None:
            print("Database connection not available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find user
        user = users_collection.find_one({'email': email})
        print(f"User found: {user is not None}")
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        print(f"User role: {user['role']}")
        
        # Create access token with consistent secret
        access_token = create_access_token(
            identity=str(user['_id']),
            additional_claims={'role': user['role'], 'email': user['email']}
        )
        
        print(f"JWT token created successfully")
        print(f"Token: {access_token[:50]}...")
        print(f"Using JWT Secret: {JWT_SECRET}")
        
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Only admin can view all users
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        users = list(users_collection.find({}, {'password': 0}))  # Exclude password
        
        # Convert ObjectId to string
        for user in users:
            user['_id'] = str(user['_id'])
        
        return jsonify({'users': users}), 200
        
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/team', methods=['GET'])
@jwt_required()
def get_team():
    """Get team members - accessible to all authenticated users"""
    try:
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # All authenticated users can view team members
        # Filter to show only team members (users with specific roles or criteria)
        team_members = list(users_collection.find(
            {'role': {'$in': ['admin', 'user']}},  # Include all roles for now
            {'password': 0}  # Exclude password
        ))
        
        # Convert ObjectId to string
        for user in team_members:
            user['_id'] = str(user['_id'])
        
        print(f"Team endpoint: Found {len(team_members)} team members")
        
        return jsonify({'users': team_members}), 200
        
    except Exception as e:
        print(f"Get team error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/users', methods=['GET'])
def debug_all_users():
    """Debug endpoint to check all users in database - NO JWT required for troubleshooting"""
    try:
        print(f"=== DEBUG ALL USERS (NO JWT) ===")
        
        # Check database connection
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection not available',
                'db_status': 'disconnected'
            }), 500
        
        # Get all users in database
        all_users = list(users_collection.find({}, {'password': 0}))
        
        print(f"Total users in database: {len(all_users)}")
        
        for user in all_users:
            user['_id'] = str(user['_id'])
            print(f"User: {user['email']} - Role: {user['role']} - Username: {user['username']}")
        
        # Count by categories
        admin_count = len([u for u in all_users if u['role'] == 'admin'])
        user_count = len([u for u in all_users if u['role'] == 'user'])
        tmis_count = len([u for u in all_users if u['email'].startswith('tmis.')])
        tmis_users = len([u for u in all_users if u['email'].startswith('tmis.') and u['role'] == 'user'])
        
        print(f"Admin users: {admin_count}")
        print(f"Regular users: {user_count}")
        print(f"TMIS email users: {tmis_count}")
        print(f"TMIS users with user role: {tmis_users}")
        
        return jsonify({
            'success': True,
            'users': all_users,
            'counts': {
                'total': len(all_users),
                'admin': admin_count,
                'user': user_count,
                'tmis_email': tmis_count,
                'tmis_users': tmis_users
            }
        }), 200
        
    except Exception as e:
        print(f"Error in debug_all_users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/database', methods=['GET'])
def debug_database():
    """Debug endpoint to check database connectivity and data"""
    try:
        # Check database connection
        if db is None:
            return jsonify({
                'status': 'error',
                'message': 'Database connection not available',
                'db_status': 'disconnected'
            }), 500
        
        # Test database connection
        try:
            db.command("ping")
            db_status = 'connected'
        except Exception as ping_error:
            return jsonify({
                'status': 'error',
                'message': f'Database ping failed: {str(ping_error)}',
                'db_status': 'ping_failed'
            }), 500
        
        # Get collection names
        collections = db.list_collection_names()
        
        # Count documents in each collection
        collection_stats = {}
        for collection_name in collections:
            try:
                count = db[collection_name].count_documents({})
                collection_stats[collection_name] = count
            except Exception as e:
                collection_stats[collection_name] = f"Error: {str(e)}"
        
        # Sample data from users and clients collections
        sample_data = {}
        
        # Sample users (without passwords)
        if 'users' in collections:
            try:
                sample_users = list(db.users.find({}, {'password': 0}).limit(3))
                for user in sample_users:
                    user['_id'] = str(user['_id'])
                sample_data['users'] = sample_users
            except Exception as e:
                sample_data['users'] = f"Error: {str(e)}"
        
        # Sample clients
        if 'clients' in collections:
            try:
                sample_clients = list(db.clients.find({}).limit(3))
                for client in sample_clients:
                    client['_id'] = str(client['_id'])
                sample_data['clients'] = sample_clients
            except Exception as e:
                sample_data['clients'] = f"Error: {str(e)}"
        
        return jsonify({
            'status': 'success',
            'db_status': db_status,
            'collections': collections,
            'collection_stats': collection_stats,
            'sample_data': sample_data,
            'mongodb_uri': os.getenv('MONGODB_URI', 'Not set')
        }), 200
        
    except Exception as e:
        print(f"Error in debug_database: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-jwt', methods=['GET'])
@jwt_required()
def test_jwt():
    """Test endpoint to verify JWT token validation is working"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'message': 'JWT token is valid',
            'user_id': current_user_id,
            'claims': claims,
            'jwt_secret_used': JWT_SECRET,
            'status': 'success'
        }), 200
        
    except Exception as e:
        print(f"JWT test error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-routes', methods=['GET'])
def test_routes():
    """Test endpoint to verify routes are registered"""
    try:
        # Get all registered routes
        routes = []
        api_routes = []
        for rule in app.url_map.iter_rules():
            route_info = {
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            }
            routes.append(route_info)
            
            # Separate API routes
            if str(rule).startswith('/api/'):
                api_routes.append(route_info)
        
        # Check for critical endpoints
        critical_endpoints = ['/api/clients', '/api/enquiries', '/api/health', '/api/status']
        endpoint_status = {}
        for endpoint in critical_endpoints:
            found = any(endpoint in route['path'] for route in api_routes)
            endpoint_status[endpoint] = 'FOUND' if found else 'MISSING'
        
        return jsonify({
            'status': 'success',
            'message': 'Routes test endpoint',
            'total_routes': len(routes),
            'api_routes_count': len(api_routes),
            'critical_endpoints': endpoint_status,
            'api_routes': sorted(api_routes, key=lambda x: x['path']),
            'blueprints_registered': list(app.blueprints.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Routes test error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/cors', methods=['GET', 'OPTIONS'])
def debug_cors():
    """Debug CORS configuration and request headers"""
    origin = request.headers.get('Origin', 'No Origin Header')
    
    return jsonify({
        'message': 'CORS Debug Endpoint',
        'request_origin': origin,
        'allowed_origins': allowed_origins,
        'request_headers': dict(request.headers),
        'cors_configured': True,
        'flask_env': os.getenv('FLASK_ENV', 'development'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/debug/production', methods=['GET'])
def debug_production():
    """Comprehensive production debugging endpoint"""
    try:
        # Environment check
        env_status = {
            'MONGODB_URI': 'SET' if os.getenv('MONGODB_URI') else 'MISSING',
            'JWT_SECRET_KEY': 'SET' if os.getenv('JWT_SECRET_KEY') else 'MISSING',
            'FLASK_ENV': os.getenv('FLASK_ENV', 'NOT_SET'),
            'CLOUDINARY_ENABLED': os.getenv('CLOUDINARY_ENABLED', 'NOT_SET'),
        }
        
        # Database status
        db_status = {
            'connection': 'UNKNOWN',
            'collections': {},
            'error': None
        }
        
        try:
            if db is not None:
                db.command("ping")
                db_status['connection'] = 'CONNECTED'
                
                # Check collections
                collections = ['users', 'clients', 'enquiries']
                for collection_name in collections:
                    try:
                        count = db[collection_name].count_documents({})
                        db_status['collections'][collection_name] = count
                    except Exception as col_error:
                        db_status['collections'][collection_name] = f'ERROR: {str(col_error)}'
            else:
                db_status['connection'] = 'NOT_CONNECTED'
                db_status['error'] = 'Database object is None'
        except Exception as db_error:
            db_status['connection'] = 'ERROR'
            db_status['error'] = str(db_error)
        
        # Routes check
        api_routes = []
        for rule in app.url_map.iter_rules():
            if str(rule).startswith('/api/'):
                api_routes.append({
                    'path': str(rule),
                    'methods': list(rule.methods),
                    'endpoint': rule.endpoint
                })
        
        # Blueprint status
        blueprint_status = {
            'registered': list(app.blueprints.keys()),
            'count': len(app.blueprints)
        }
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': env_status,
            'database': db_status,
            'routes': {
                'api_routes_count': len(api_routes),
                'api_routes': api_routes[:10],  # First 10 routes
                'critical_endpoints': {
                    '/api/clients': any('/api/clients' in route['path'] for route in api_routes),
                    '/api/enquiries': any('/api/enquiries' in route['path'] for route in api_routes),
                    '/api/health': any('/api/health' in route['path'] for route in api_routes),
                }
            },
            'blueprints': blueprint_status,
            'system': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'working_directory': os.getcwd()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Debug endpoint failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Import and register client routes
try:
    print("🔄 Importing client routes...")
    from client_routes import client_bp
    app.register_blueprint(client_bp, url_prefix='/api')
    print("✅ Client routes registered successfully")
except Exception as e:
    print(f"❌ Error importing client routes: {e}")
    
    # Create a simple fallback client endpoint
    @app.route('/api/clients', methods=['GET'])
    @jwt_required()
    def get_clients_fallback():
        try:
            print("=== FALLBACK CLIENTS ENDPOINT ===")
            
            # Get JWT claims for debugging
            claims = get_jwt()
            current_user_id = get_jwt_identity()
            user_role = claims.get('role', 'user')
            user_email = claims.get('email', current_user_id)
            
            print(f"User ID: {current_user_id}")
            print(f"User Role: {user_role}")
            print(f"User Email: {user_email}")
            
            # Check database connection
            if db is None:
                print("Database connection not available")
                return jsonify({
                    'error': 'Database connection failed', 
                    'clients': [],
                    'fallback': True,
                    'debug_info': {
                        'user_id': current_user_id,
                        'user_role': user_role,
                        'db_status': 'disconnected'
                    }
                }), 500
            
            try:
                db.command("ping")
                print("Database connection successful")
            except Exception as db_error:
                print(f"Database connection failed: {str(db_error)}")
                return jsonify({'error': 'Database connection failed', 'clients': []}), 500
            
            # Get clients from database
            try:
                if user_role == 'admin':
                    # Admin can see all clients
                    clients_cursor = clients_collection.find()
                    print("Admin user - fetching all clients")
                else:
                    # Regular users see only their clients
                    clients_cursor = clients_collection.find({'created_by': current_user_id})
                    print(f"Regular user - fetching clients for: {current_user_id}")
                
                clients_list = []
                for client in clients_cursor:
                    # Convert ObjectId to string
                    client['_id'] = str(client['_id'])
                    clients_list.append(client)
                
                print(f"Found {len(clients_list)} clients")
                
                return jsonify({
                    'clients': clients_list,
                    'fallback': True,
                    'message': 'Using fallback endpoint - client_routes import failed',
                    'count': len(clients_list)
                }), 200
                
            except Exception as db_error:
                print(f"Database query error: {str(db_error)}")
                return jsonify({
                    'error': f'Database query failed: {str(db_error)}',
                    'clients': [],
                    'fallback': True
                }), 500
                
        except Exception as fallback_error:
            print(f"Fallback endpoint error: {str(fallback_error)}")
            return jsonify({
                'error': f'Fallback endpoint failed: {str(fallback_error)}',
                'clients': [],
                'fallback': True
            }), 500

# Import and register enquiry routes
try:
    print("🔄 Importing enquiry routes...")
    from enquiry_routes import enquiry_bp
    app.register_blueprint(enquiry_bp, url_prefix='/api')
    print("✅ Enquiry routes registered successfully")
except Exception as e:
    print(f"❌ Error importing enquiry routes: {e}")
    
    # Create a simple fallback enquiry endpoint
    @app.route('/api/enquiries', methods=['GET'])
    @jwt_required()
    def get_enquiries_fallback():
        try:
            print("=== FALLBACK ENQUIRIES ENDPOINT ===")
            
            # Get JWT claims for debugging
            claims = get_jwt()
            current_user_id = get_jwt_identity()
            user_role = claims.get('role', 'user')
            
            print(f"User ID: {current_user_id}")
            print(f"User Role: {user_role}")
            
            # Check database connection
            if db is None:
                return jsonify({
                    'error': 'Database connection failed', 
                    'enquiries': [],
                    'fallback': True
                }), 500
            
            try:
                db.command("ping")
                print("Database connection successful")
            except Exception as db_error:
                print(f"Database connection failed: {str(db_error)}")
                return jsonify({'error': 'Database connection failed', 'enquiries': []}), 500
            
            # Get enquiries from database
            try:
                enquiries_collection = db.enquiries
                
                if user_role == 'admin':
                    # Admin can see all enquiries
                    enquiries_cursor = enquiries_collection.find()
                    print("Admin user - fetching all enquiries")
                else:
                    # Regular users see only their enquiries
                    enquiries_cursor = enquiries_collection.find({'created_by': current_user_id})
                    print(f"Regular user - fetching enquiries for: {current_user_id}")
                
                enquiries_list = []
                for enquiry in enquiries_cursor:
                    # Convert ObjectId to string
                    enquiry['_id'] = str(enquiry['_id'])
                    enquiries_list.append(enquiry)
                
                print(f"Found {len(enquiries_list)} enquiries")
                
                return jsonify({
                    'enquiries': enquiries_list,
                    'fallback': True,
                    'message': 'Using fallback endpoint - enquiry_routes import failed',
                    'count': len(enquiries_list)
                }), 200
                
            except Exception as db_error:
                print(f"Database query error: {str(db_error)}")
                return jsonify({
                    'error': f'Database query failed: {str(db_error)}',
                    'enquiries': [],
                    'fallback': True
                }), 500
                
        except Exception as fallback_error:
            print(f"Fallback enquiry endpoint error: {str(fallback_error)}")
            return jsonify({
                'error': f'Fallback enquiry endpoint failed: {str(fallback_error)}',
                'enquiries': [],
                'fallback': True
            }), 500

# Export app for main.py to use
