from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
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

# Initialize extensions
CORS(app, origins=["http://localhost:4200", "http://localhost:4201", "https://tmis-business-guru.vercel.app"], supports_credentials=True)
jwt = JWTManager(app)

# JWT Error Handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT Token expired")
    return jsonify({'msg': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"JWT Invalid token: {error}")
    return jsonify({'msg': 'Invalid token'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"JWT Missing token: {error}")
    return jsonify({'msg': 'Authorization token is required'}), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    print("JWT Token revoked")
    return jsonify({'msg': 'Token has been revoked'}), 401

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    print("❌ CRITICAL ERROR: MONGODB_URI environment variable not found!")
    print("Please set MONGODB_URI in your environment variables or .env file")
    print("Example: MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/database_name")
    raise Exception("MONGODB_URI environment variable is required")

print(f"🔄 Connecting to MongoDB...")
print(f"MongoDB URI: {MONGODB_URI[:50]}...{MONGODB_URI[-20:]}")  # Hide credentials in logs

try:
    client = MongoClient(MONGODB_URI)
    db = client.tmis_business_guru
    # Test connection
    db.command("ping")
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {str(e)}")
    print("🔍 Troubleshooting:")
    print("1. Check if MongoDB URI includes database name")
    print("2. Verify MongoDB Atlas cluster is running")
    print("3. Check network connectivity and IP whitelist")
    print("4. Verify credentials in MongoDB URI")
    raise Exception(f"Failed to connect to MongoDB: {str(e)}")

# Collections
if db is not None:
    users_collection = db.users
    clients_collection = db.clients
else:
    users_collection = None
    clients_collection = None

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
        if db is None or users_collection is None:
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
        if db is None or users_collection is None:
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
        if db is None or users_collection is None:
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
        if db is None or users_collection is None:
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
        if db is None or users_collection is None:
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

# Export app for main.py to use
