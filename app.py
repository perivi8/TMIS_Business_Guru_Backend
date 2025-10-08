from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from flask_socketio import SocketIO, emit, join_room, leave_room
import bcrypt
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import smtplib
import email.mime.text
import email.mime.multipart
import sys
import uuid
import threading
import time
from bson.json_util import dumps

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

# Configure CORS with more flexible settings to handle Vercel deployments
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
        # Add wildcard pattern to catch all Vercel deployments
        "https://*.vercel.app"
    ]
    allowed_origins.extend(vercel_domains)
    print(f"🔧 Production mode: Added Vercel domains to CORS")

print(f"🌐 CORS Allowed Origins: {allowed_origins}")
print(f"🔧 Flask Environment: {flask_env}")

# Configure CORS with specific origins only (no wildcards with credentials)
cors.init_app(app, 
    origins=allowed_origins,  # Always use specific origins
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control"],
    supports_credentials=True,
    expose_headers=[
        "Content-Disposition",
        "Authorization",
        "Access-Control-Allow-Origin"
    ],
    send_wildcard=False,  # Cannot use wildcard with credentials
    automatic_options=True,
    max_age=86400  # Cache preflight for 24 hours
)
jwt = JWTManager(app)

# Initialize SocketIO with CORS support
socketio = SocketIO(
    app,
    cors_allowed_origins="*",  # Allow all origins for development
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    transports=['polling', 'websocket'],
    allow_upgrades=True,
    ping_timeout=60,
    ping_interval=25
)

# Store for pending approval requests
pending_approvals = {}
admin_sessions = {}

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

@app.route('/api/cors-debug', methods=['GET', 'POST', 'OPTIONS'])
def cors_debug():
    """Debug endpoint to check CORS configuration"""
    origin = request.headers.get('Origin', 'No Origin Header')
    content_type = request.headers.get('Content-Type', 'No Content-Type Header')
    
    return jsonify({
        'message': 'CORS Debug Endpoint',
        'method': request.method,
        'request_origin': origin,
        'content_type': content_type,
        'allowed_origins': allowed_origins,
        'request_headers': dict(request.headers),
        'cors_configured': True,
        'flask_env': flask_env,
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

# Log protected endpoint requests for debugging (CORS handled by Flask-CORS)
@app.before_request
def handle_requests():
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

# Simplified after_request handler for dynamic Vercel origins only
@app.after_request
def after_request_cors_handler(response):
    """Handle dynamic CORS for new Vercel deployments only"""
    try:
        origin = request.headers.get('Origin')
        
        # Only handle new Vercel origins that aren't in the static allowed_origins list
        if (flask_env == 'production' and origin and 'vercel.app' in origin and 
            origin not in allowed_origins):
            # Check if Flask-CORS already set the origin
            if not response.headers.get('Access-Control-Allow-Origin'):
                response.headers['Access-Control-Allow-Origin'] = origin
                print(f"🔧 Added dynamic CORS origin: {origin}")
            
        return response
    except Exception as e:
        print(f"CORS after_request error: {e}")
        return response

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
    pending_registrations_collection = db.pending_registrations
    
    # Test collections access
    try:
        user_count = users_collection.count_documents({})
        client_count = clients_collection.count_documents({})
        pending_registrations_count = pending_registrations_collection.count_documents({})
        print(f"📊 Database stats: {user_count} users, {client_count} clients, {pending_registrations_count} pending registrations")
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
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        print(f"📧 Attempting to send email to: {to_email}")
        print(f"📧 SMTP Server: {smtp_server}:{smtp_port}")
        print(f"📧 From Email: {smtp_email}")
        
        # Check if all required SMTP configuration is available
        if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
            print("❌ Missing SMTP configuration")
            return False
        
        # Convert port to integer
        try:
            smtp_port = int(smtp_port)
        except (ValueError, TypeError):
            print("❌ Invalid SMTP port")
            return False
        
        msg = email.mime.multipart.MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(email.mime.text.MIMEText(body, 'html'))
        
        print(f"📧 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print(f"📧 Logging in...")
        server.login(smtp_email, smtp_password)
        
        print(f"📧 Sending email...")
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {str(e)}")
        print("💡 Check your email and app password in .env file")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ Recipient email refused: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if data is provided
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        
        if not all([username, email, password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        # Check database connection
        if db is None or users_collection is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Check if user already exists in users collection (approved users only)
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400
        
        # Check if there's already a pending registration for this email
        if pending_registrations_collection is not None:
            existing_pending = pending_registrations_collection.find_one({'email': email})
            if existing_pending:
                # Delete the old pending registration to allow re-registration
                pending_registrations_collection.delete_one({'email': email})
                print(f"🔄 Removed old pending registration for {email}")
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create pending registration (NOT in users collection)
        registration_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'role': 'user',
            'created_at': datetime.utcnow(),
            'session_id': str(ObjectId())  # For tracking
        }
        
        if pending_registrations_collection is not None:
            result = pending_registrations_collection.insert_one(registration_data)
        
        # Send notification to admin about new registration
        try:
            if users_collection is not None:
                admin_users = list(users_collection.find({'role': 'admin', 'status': 'active'}))
                for admin in admin_users:
                    admin_email = admin.get('email')
                    if admin_email:
                        subject = "New User Registration Pending Approval"
                        body = f"""
                        <html>
                        <body>
                            <h2>New User Registration</h2>
                            <p>A new user has registered and is pending approval:</p>
                            <ul>
                                <li><strong>Username:</strong> {username}</li>
                                <li><strong>Email:</strong> {email}</li>
                                <li><strong>Registration Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</li>
                            </ul>
                            <p>Please log in to the admin dashboard to approve or reject this registration.</p>
                        </body>
                        </html>
                        """
                        send_email(admin_email, subject, body)
        except Exception as email_error:
            print(f"Failed to send admin notification email: {email_error}")
        
        return jsonify({
            'message': 'Registration request submitted. Waiting for admin verification...',
            'registration_id': str(result.inserted_id) if 'result' in locals() else 'unknown',
            'status': 'waiting_approval'
        }), 201
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        # Check if data is provided
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        print(f"=== LOGIN DEBUG ===")
        print(f"Login attempt for email: {email}")
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Check database connection
        if db is None or users_collection is None:
            print("Database connection not available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find user
        user = users_collection.find_one({'email': email})
        print(f"User found: {user is not None}")
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Handle users without status (existing users) - set them as active
        if 'status' not in user or user.get('status') is None:
            users_collection.update_one(
                {'_id': user['_id']},
                {'$set': {'status': 'active'}}
            )
            user['status'] = 'active'
        
        # Check if user is pending approval
        if user.get('status') == 'pending':
            return jsonify({'error': 'Your account is pending admin approval. Please wait for approval.'}), 403
        
        # Check if user is rejected
        if user.get('status') == 'rejected':
            return jsonify({'error': 'Your account has been rejected. Please contact admin.'}), 403
        
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
        
        # Get all users
        users = list(users_collection.find({}, {'password': 0}))
        
        # Convert ObjectId to string
        for user in users:
            user['_id'] = str(user['_id'])
        
        return jsonify({'users': users}), 200
        
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': str(e)}), 500


@app.before_request
def check_deleted_users():
    """Check if the current user has been deleted and should be logged out"""
    try:
        # Skip for non-authenticated endpoints
        if request.endpoint in ['login', 'register', 'check_registration_status', 'debug_database']:
            return
        
        # Skip for OPTIONS requests
        if request.method == 'OPTIONS':
            return
            
        # Get the authorization header
        auth_header = request.headers.get('Authorization')
        
        # Check if auth header exists and has the right format
        if not auth_header or not auth_header.startswith('Bearer '):
            return
            
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Decode token to get user info
        try:
            from flask_jwt_extended import decode_token
            decoded_token = decode_token(token)
            user_id = decoded_token.get('sub')
            user_email = decoded_token.get('email')
            
            # Check if user is in deleted users cache
            deleted_users_cache = getattr(app, 'deleted_users_cache', set())
            
            if user_id in deleted_users_cache or user_email in deleted_users_cache:
                print(f"🚫 Blocking request from deleted user: {user_email}")
                return jsonify({
                    'error': 'user_deleted',
                    'message': 'Your account has been deleted. Please contact admin.',
                    'logout_required': True
                }), 401
        except Exception as decode_error:
            # Invalid token, let the normal JWT handling deal with it
            pass
            
    except Exception as e:
        print(f"Check deleted users error: {e}")
        # Don't block the request if there's an error in this check
        pass

@app.route('/api/team', methods=['GET'])
@jwt_required()
def get_team():
    """Get team members - accessible to all authenticated users"""
    try:
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # All authenticated users can view team members
        # Only show approved/active users (explicitly exclude pending and rejected)
        team_members = list(users_collection.find(
            {
                'role': {'$in': ['admin', 'user']},
                '$and': [
                    {'status': {'$ne': 'pending'}},    # Exclude pending users
                    {'status': {'$ne': 'rejected'}},   # Exclude rejected users
                    {'$or': [
                        {'status': 'active'},
                        {'status': {'$exists': False}}  # Legacy users without status field
                    ]}
                ]
            },
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

@app.route('/api/debug/all-users', methods=['GET'])
@jwt_required()
def debug_all_users():
    """Debug endpoint to see all users and their statuses - Admin only"""
    try:
        # Check if user is admin
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get all users with their statuses
        all_users = list(users_collection.find(
            {},
            {'password': 0}  # Exclude password
        ))
        
        # Convert ObjectId to string and add debug info
        for user in all_users:
            user['_id'] = str(user['_id'])
            user['debug_status'] = user.get('status', 'NO_STATUS')
        
        print(f"Debug: Found {len(all_users)} total users in database")
        for user in all_users:
            print(f"  - {user.get('username')} ({user.get('email')}) - Status: {user.get('debug_status')}")
        
        return jsonify({'users': all_users, 'total_count': len(all_users)}), 200
        
    except Exception as e:
        print(f"Debug all users error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup/rejected-users', methods=['DELETE'])
@jwt_required()
def cleanup_rejected_users():
    """Remove all rejected users from database - Admin only"""
    try:
        # Check if user is admin
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find rejected users first
        rejected_users = list(users_collection.find({'status': 'rejected'}))
        print(f"Found {len(rejected_users)} rejected users to remove:")
        for user in rejected_users:
            print(f"  - {user.get('username')} ({user.get('email')})")
        
        # Delete rejected users
        result = users_collection.delete_many({'status': 'rejected'})
        
        print(f"Deleted {result.deleted_count} rejected users")
        
        return jsonify({
            'message': f'Successfully removed {result.deleted_count} rejected users',
            'deleted_count': result.deleted_count,
            'rejected_users': [{'username': u.get('username'), 'email': u.get('email')} for u in rejected_users]
        }), 200
        
    except Exception as e:
        print(f"Cleanup rejected users error: {e}")
        return jsonify({'error': str(e)}), 500

# Emergency cleanup endpoint removed for security

@app.route('/api/user-status', methods=['GET'])
@jwt_required()
def check_user_status():
    """Check if current user still exists and is active"""
    try:
        current_user_id = get_jwt_identity()
        
        # Check if user exists in database
        user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        
        if not user:
            return jsonify({
                'error': 'user_deleted',
                'message': 'Your account has been deleted. Please contact admin.',
                'logout_required': True
            }), 401
        
        return jsonify({
            'status': 'active',
            'message': 'User is active'
        }), 200
        
    except Exception as e:
        print(f"User status check error: {e}")
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

# User approval endpoints
@app.route('/api/pending-users', methods=['GET'])
@jwt_required()
def get_pending_users():
    """Get all pending user registrations - Admin only"""
    try:
        # Check if user is admin
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get pending registrations
        pending_users = list(pending_registrations_collection.find(
            {}, 
            {'password': 0}  # Exclude password
        ))
        
        # Convert ObjectId to string
        for user in pending_users:
            user['_id'] = str(user['_id'])
        
        return jsonify({'pending_users': pending_users}), 200
        
    except Exception as e:
        print(f"Get pending users error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/approve-user/<user_id>', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    """Approve a pending user registration - Admin only"""
    try:
        print(f"🔍 Approve user request for ID: {user_id}")
        
        # Check if user is admin
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Validate ObjectId format
        try:
            obj_id = ObjectId(user_id)
        except Exception as e:
            print(f"❌ Invalid ObjectId format: {user_id}, error: {e}")
            return jsonify({'error': 'Invalid user ID format'}), 400
        
        print(f"🔍 Looking for user with ObjectId: {obj_id}")
        
        # Find the pending registration
        pending_registration = pending_registrations_collection.find_one({'_id': obj_id})
        if not pending_registration:
            print(f"❌ No pending registration found with ID: {user_id}")
            return jsonify({'error': 'Pending registration not found'}), 404
        
        print(f"✅ Found pending registration: {pending_registration.get('username')} ({pending_registration.get('email')})")
        
        # Get admin info
        admin_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        admin_name = admin_user.get('username', 'Admin') if admin_user else 'Admin'
        
        # Create approved user in users collection
        user_data = {
            'username': pending_registration['username'],
            'email': pending_registration['email'],
            'password': pending_registration['password'],
            'role': pending_registration['role'],
            'status': 'active',
            'created_at': pending_registration['created_at'],
            'approved_at': datetime.utcnow(),
            'approved_by': current_user_id
        }
        
        # Insert into users collection
        result = users_collection.insert_one(user_data)
        
        # Remove from pending registrations
        pending_registrations_collection.delete_one({'_id': obj_id})
        
        if not result.inserted_id:
            return jsonify({'error': 'Failed to approve user'}), 500
        
        # Send approval email to user
        try:
            subject = "Account Approved - TMIS Business Guru"
            body = f"""
            <html>
            <body>
                <h2>Account Approved!</h2>
                <p>Dear {pending_registration['username']},</p>
                <p>Your account registration has been approved by {admin_name}.</p>
                <p>You can now log in to your account using your email and password.</p>
                <p><strong>Login URL:</strong> <a href="https://tmis-business-guru.vercel.app/login">Login Here</a></p>
                <p>Thank you for joining TMIS Business Guru!</p>
            </body>
            </html>
            """
            send_email(pending_registration['email'], subject, body)
        except Exception as email_error:
            print(f"Failed to send approval email: {email_error}")
        
        return jsonify({
            'message': 'User approved successfully',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        print(f"Approve user error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-user/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete a user - Admin only"""
    try:
        print(f"🗑️ Delete user request for ID: {user_id}")
        
        # Check if user is admin
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Validate ObjectId format
        try:
            obj_id = ObjectId(user_id)
        except Exception as e:
            print(f"❌ Invalid ObjectId format: {user_id}, error: {e}")
            return jsonify({'error': 'Invalid user ID format'}), 400
        
        # Prevent admin from deleting themselves
        if user_id == current_user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Find the user to delete
        user_to_delete = users_collection.find_one({'_id': obj_id})
        if not user_to_delete:
            print(f"❌ No user found with ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404
        
        # Prevent deleting other admins (optional security measure)
        if user_to_delete.get('role') == 'admin':
            return jsonify({'error': 'Cannot delete admin users'}), 403
        
        print(f"✅ Found user to delete: {user_to_delete.get('username')} ({user_to_delete.get('email')})")
        
        # Store user info before deletion for logout
        deleted_user_email = user_to_delete.get('email')
        deleted_user_id = str(user_to_delete.get('_id'))
        
        # Delete the user
        result = users_collection.delete_one({'_id': obj_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Failed to delete user'}), 500
        
        print(f"✅ Successfully deleted user: {user_to_delete.get('username')}")
        
        # Add the deleted user to a blacklist for immediate logout
        # This will be checked by the auth middleware
        deleted_users_cache = getattr(app, 'deleted_users_cache', set())
        deleted_users_cache.add(deleted_user_id)
        deleted_users_cache.add(deleted_user_email)
        app.deleted_users_cache = deleted_users_cache
        
        print(f"🚫 Added user to logout blacklist: {deleted_user_email}")
        
        # Schedule cleanup of the blacklist after 1 hour to prevent memory leaks
        import threading
        def cleanup_blacklist():
            import time
            time.sleep(3600)  # Wait 1 hour
            try:
                cache = getattr(app, 'deleted_users_cache', set())
                cache.discard(deleted_user_id)
                cache.discard(deleted_user_email)
                print(f"🧹 Cleaned up blacklist entry for: {deleted_user_email}")
            except:
                pass
        
        cleanup_thread = threading.Thread(target=cleanup_blacklist, daemon=True)
        cleanup_thread.start()
        
        return jsonify({
            'message': f'User {user_to_delete.get("username")} deleted successfully',
            'deleted_user_id': deleted_user_id,
            'deleted_user_email': deleted_user_email
        }), 200
        
    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reject-user/<user_id>', methods=['POST'])
@jwt_required()
def reject_user(user_id):
    """Reject a pending user registration - Admin only"""
    try:
        print(f"🗑️ Reject user request for ID: {user_id}")
        # Check if user is admin
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        if claims.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        data = request.get_json()
        rejection_reason = data.get('reason', 'No reason provided')
        
        # Validate ObjectId format
        try:
            obj_id = ObjectId(user_id)
        except Exception as e:
            print(f"❌ Invalid ObjectId format: {user_id}, error: {e}")
            return jsonify({'error': 'Invalid user ID format'}), 400
        
        # Find the pending registration
        pending_registration = pending_registrations_collection.find_one({'_id': obj_id})
        if not pending_registration:
            print(f"❌ No pending registration found with ID: {user_id}")
            return jsonify({'error': 'Pending registration not found'}), 404
        
        print(f"✅ Found pending registration: {pending_registration.get('username')} ({pending_registration.get('email')})")
        
        # Get admin info
        admin_user = users_collection.find_one({'_id': ObjectId(current_user_id)})
        admin_name = admin_user.get('username', 'Admin') if admin_user else 'Admin'
        
        # Delete the pending registration (rejection means removal)
        result = pending_registrations_collection.delete_one({'_id': obj_id})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Failed to reject user'}), 500
        
        print(f"✅ Successfully rejected registration: {pending_registration.get('username')}")
        
        # Send rejection email to user
        try:
            subject = "Account Registration - TMIS Business Guru"
            body = f"""
            <html>
            <body>
                <h2>Account Registration Update</h2>
                <p>Dear {pending_registration['username']},</p>
                <p>We regret to inform you that your account registration has been declined.</p>
                <p><strong>Reason:</strong> {rejection_reason}</p>
                <p>If you have any questions, please contact our support team.</p>
            </body>
            </html>
            """
            send_email(pending_registration['email'], subject, body)
        except Exception as email_error:
            print(f"Failed to send rejection email: {email_error}")
        
        return jsonify({
            'message': 'User rejected successfully',
            'user_id': user_id
        }), 200
        
    except Exception as e:
        print(f"Reject user error: {e}")
        return jsonify({'error': str(e)}), 500

# Forgot password endpoints
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset code to user's email"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        print(f"🔍 Looking for user with email: {email}")
        
        # First check if user exists at all
        user_any_status = users_collection.find_one({'email': email})
        print(f"🔍 User found (any status): {user_any_status is not None}")
        
        if user_any_status:
            print(f"🔍 User status: {user_any_status.get('status', 'No status field')}")
            print(f"🔍 User details: {user_any_status.get('username', 'No username')}")
        
        # Find user - check both active users and users without status (legacy users)
        user = users_collection.find_one({
            'email': email, 
            '$or': [
                {'status': 'active'},
                {'status': {'$exists': False}}  # Legacy users without status field
            ]
        })
        
        if not user:
            print(f"❌ No active user found for email: {email}")
            # Return error for non-existent users (as requested)
            return jsonify({'error': 'Email not found. Only registered users can reset their password.'}), 404
        
        print(f"✅ Found user: {user.get('username')} with status: {user.get('status', 'legacy')}")
        
        # Generate 6-digit reset code
        import random
        reset_code = str(random.randint(100000, 999999))
        # Store reset code with expiration (15 minutes)
        reset_data = {
            'user_id': str(user['_id']),
            'email': email,
            'reset_code': reset_code,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=15),
            'used': False
        }
        
        # Create or update reset collection
        reset_collection = db.password_resets
        reset_collection.insert_one(reset_data)
        
        # Send reset code email
        try:
            subject = "Password Reset Code - TMIS Business Guru"
            body = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Dear {user['username']},</p>
                <p>You have requested to reset your password. Please use the following code:</p>
                <h3 style="color: #007bff; font-size: 24px; letter-spacing: 2px;">{reset_code}</h3>
                <p><strong>This code will expire in 15 minutes.</strong></p>
                <p>If you didn't request this reset, please ignore this email.</p>
            </body>
            </html>
            """
            
            print(f"Sending reset code {reset_code} to {email}")
            email_sent = send_email(email, subject, body)
            
            if not email_sent:
                print(f"Email sending failed for {email}")
                return jsonify({'error': 'Failed to send reset code. Please check your email address.'}), 500
                
            print(f"✅ Email sent successfully to {email}")
            
            # Return success response
            return jsonify({
                'message': 'Password reset code sent successfully. Please check your email.',
                'email': email
            }), 200
            
        except Exception as email_error:
            print(f"Failed to send reset code email: {email_error}")
            return jsonify({'error': 'Failed to send reset code. Please try again later.'}), 500
        
    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({'error': str(e)}), 500

# Test SMTP configuration endpoint
@app.route('/api/test-smtp', methods=['POST'])
@jwt_required()
def test_smtp():
    """Test SMTP email configuration"""
    try:
        data = request.get_json()
        test_email = data.get('email')
        
        if not test_email:
            return jsonify({'error': 'Email is required'}), 400
        
        subject = "SMTP Test - TMIS Business Guru"
        body = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email to verify SMTP configuration is working correctly.</p>
            <p>If you received this email, your SMTP settings are configured properly!</p>
            <p><strong>TMIS Business Guru System</strong></p>
        </body>
        </html>
        """
        
        print(f"Testing SMTP with email: {test_email}")
        email_sent = send_email(test_email, subject, body)
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully!',
                'email': test_email
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test email. Check SMTP configuration.',
                'email': test_email
            }), 500
            
    except Exception as e:
        print(f"SMTP test error: {e}")
        return jsonify({'error': f'SMTP test failed: {str(e)}'}), 500

# Add endpoint to check user registration status
@app.route('/api/check-registration-status/<email>', methods=['GET'])
def check_registration_status(email):
    """Check the registration status of a user by email"""
    try:
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # First check if user exists in users collection (approved)
        user = users_collection.find_one({'email': email})
        
        if user:
            user_status = user.get('status', 'active')  # Default to active for legacy users
        else:
            # Check if there's a pending registration
            pending_registration = pending_registrations_collection.find_one({'email': email})
            if pending_registration:
                user_status = 'pending'
                user = pending_registration  # Use pending registration data
            else:
                return jsonify({
                    'status': 'not_registered',
                    'message': 'Email not found. Please register first.'
                }), 404
        
        status_messages = {
            'pending': 'Your registration is pending admin approval. Please wait for approval.',
            'active': 'Your account is approved and active. You can log in.',
            'rejected': 'Your registration was rejected. Please contact admin for more information.'
        }
        
        return jsonify({
            'status': user_status,
            'message': status_messages.get(user_status, 'Unknown status'),
            'username': user.get('username', ''),
            'email': user.get('email', ''),
            'created_at': user.get('created_at', '').isoformat() if user.get('created_at') else ''
        }), 200
        
    except Exception as e:
        print(f"Check registration status error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """Verify the password reset code"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')
        
        if not all([email, reset_code]):
            return jsonify({'error': 'Email and reset code are required'}), 400
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find valid reset code
        reset_collection = db.password_resets
        reset_record = reset_collection.find_one({
            'email': email,
            'reset_code': reset_code,
            'used': False,
            'expires_at': {'$gt': datetime.utcnow()}
        })
        
        if not reset_record:
            return jsonify({'error': 'Invalid or expired reset code'}), 400
        
        return jsonify({
            'message': 'Reset code verified successfully',
            'valid': True
        }), 200
        
    except Exception as e:
        print(f"Verify reset code error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset user password with verified code"""
    try:
        data = request.get_json()
        email = data.get('email')
        reset_code = data.get('reset_code')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not all([email, reset_code, new_password, confirm_password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check database connection
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find and validate reset code
        reset_collection = db.password_resets
        reset_record = reset_collection.find_one({
            'email': email,
            'reset_code': reset_code,
            'used': False,
            'expires_at': {'$gt': datetime.utcnow()}
        })
        
        if not reset_record:
            return jsonify({'error': 'Invalid or expired reset code'}), 400
        
        # Find user
        user = users_collection.find_one({'email': email, 'status': 'active'})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Hash new password
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update user password
        result = users_collection.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'password': hashed_password,
                    'password_updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'Failed to update password'}), 500
        
        # Mark reset code as used
        reset_collection.update_one(
            {'_id': reset_record['_id']},
            {'$set': {'used': True, 'used_at': datetime.utcnow()}}
        )
        
        # Send confirmation email
        try:
            subject = "Password Reset Successful - TMIS Business Guru"
            body = f"""
            <html>
            <body>
                <h2>Password Reset Successful</h2>
                <p>Dear {user['username']},</p>
                <p>Your password has been successfully reset.</p>
                <p>You can now log in with your new password.</p>
                <p>If you didn't make this change, please contact support immediately.</p>
            </body>
            </html>
            """
            send_email(email, subject, body)
        except Exception as email_error:
            print(f"Failed to send confirmation email: {email_error}")
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'error': str(e)}), 500

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

# Register Chatbot Routes
try:
    print("🔄 Importing chatbot routes...")
    from chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp)
    print("✅ Chatbot routes registered successfully")
except Exception as e:
    print(f"❌ Error importing chatbot routes: {e}")
    
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

# Initialize SocketIO handlers
try:
    from socketio_handlers import init_socketio_handlers
    init_socketio_handlers(socketio, users_collection)
    print("✅ SocketIO handlers initialized successfully")
except Exception as e:
    print(f"❌ Error initializing SocketIO handlers: {e}")

# Add real-time registration endpoint
@app.route('/api/register-realtime', methods=['POST'])
def register_realtime():
    try:
        from socketio_handlers import create_approval_request
        
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')
        user_session_id = data.get('session_id')
        
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

# GreenAPI WhatsApp test endpoint
@app.route('/api/test-greenapi', methods=['POST'])
@jwt_required()
def test_greenapi_endpoint():
    """Test GreenAPI WhatsApp service"""
    try:
        data = request.get_json()
        mobile_number = data.get('mobile_number', '918106811285')
        
        # Import GreenAPI service
        from greenapi_whatsapp_service import whatsapp_service
        
        if not whatsapp_service or not whatsapp_service.api_available:
            return jsonify({
                'success': False,
                'error': 'GreenAPI service not available',
                'solution': 'Check GREENAPI_INSTANCE_ID and GREENAPI_TOKEN in .env'
            }), 500
        
        # Test message
        test_message = f"🧪 TMIS GreenAPI Test\n\nHello! This is a test message from TMIS Business Guru.\n\n✅ No OTP required\n🚀 Sent via GreenAPI\n\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        result = whatsapp_service.send_message(mobile_number, test_message)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'GreenAPI test message sent successfully',
                'message_id': result.get('message_id'),
                'mobile_number': mobile_number,
                'service': 'GreenAPI'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error'),
                'mobile_number': mobile_number,
                'service': 'GreenAPI'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        }), 500

# Main execution
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    print(f"🚀 Starting TMIS Business Guru Backend with SocketIO...")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    # For production, use production settings
    if os.environ.get('FLASK_ENV') == 'production':
        socketio.run(app, host='0.0.0.0', port=port, debug=False, log_output=False)
    else:
        socketio.run(app, host='0.0.0.0', port=port, debug=debug)

# Export app for main.py to use
