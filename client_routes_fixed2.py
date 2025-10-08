from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from werkzeug.utils import secure_filename
import os
import sys
from datetime import datetime
from bson import ObjectId
from bson.json_util import dumps
import json
from pymongo import MongoClient
from dotenv import load_dotenv
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import email_service, but make it optional
try:
    from email_service import email_service
    EMAIL_SERVICE_AVAILABLE = True
    print("✅ email_service imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: email_service not available: {e}")
    EMAIL_SERVICE_AVAILABLE = False
    email_service = None
except Exception as e:
    print(f"⚠️ Warning: email_service import failed: {e}")
    EMAIL_SERVICE_AVAILABLE = False
    email_service = None

# Try to import cloudinary, but make it optional
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
    print("✅ Cloudinary imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: Cloudinary not available: {e}")
    CLOUDINARY_AVAILABLE = False
    cloudinary = None
except Exception as e:
    print(f"⚠️ Warning: Cloudinary import failed: {e}")
    CLOUDINARY_AVAILABLE = False
    cloudinary = None

# Try to import DocumentProcessor, but make it optional
try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
    print("✅ DocumentProcessor imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: DocumentProcessor not available: {e}")
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DocumentProcessor = None
except Exception as e:
    print(f"⚠️ Warning: DocumentProcessor import failed: {e}")
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DocumentProcessor = None

# Try to import ClientWhatsAppService, but make it optional
try:
    from client_whatsapp_service import client_whatsapp_service
    WHATSAPP_SERVICE_AVAILABLE = True
    print("✅ client_whatsapp_service imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: client_whatsapp_service not available: {e}")
    WHATSAPP_SERVICE_AVAILABLE = False
    client_whatsapp_service = None
except Exception as e:
    print(f"⚠️ Warning: client_whatsapp_service import failed: {e}")
    WHATSAPP_SERVICE_AVAILABLE = False
    client_whatsapp_service = None

# Load environment variables
load_dotenv()

# Cloudinary configuration
CLOUDINARY_ENABLED = os.getenv('CLOUDINARY_ENABLED', 'false').lower() == 'true'
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

# Initialize Cloudinary if enabled and available
if CLOUDINARY_AVAILABLE and CLOUDINARY_ENABLED and CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    try:
        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True
        )
        print(f"✅ Cloudinary initialized successfully with cloud: {CLOUDINARY_CLOUD_NAME}")
    except Exception as e:
        print(f"❌ Failed to initialize Cloudinary: {str(e)}")
        CLOUDINARY_ENABLED = False
else:
    if not CLOUDINARY_AVAILABLE:
        print("⚠️ Cloudinary library not available")
    else:
        print("⚠️ Cloudinary credentials not found or incomplete")
    CLOUDINARY_ENABLED = False

# MongoDB connection for this module with error handling
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    print("❌ CRITICAL ERROR: MONGODB_URI environment variable not found in client_routes!")
    print("🔧 This will cause database operations to fail gracefully")
    # Set to None but don't crash the module - allow graceful degradation
    db = None
    clients_collection = None
    users_collection = None
else:
    print(f"🔄 Client routes connecting to MongoDB...")
    print(f"MongoDB URI: {MONGODB_URI[:50]}...{MONGODB_URI[-20:]}")  # Hide credentials in logs

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)  # 5 second timeout
        db = client.tmis_business_guru
        # Test connection
        db.command("ping")
        clients_collection = db.clients
        users_collection = db.users
        print("✅ MongoDB connection successful for client_routes module")
    except Exception as e:
        print(f"❌ MongoDB connection failed for client_routes module: {str(e)}")
        print("🔍 Troubleshooting:")
        print("1. Check if MongoDB URI includes database name")
        print("2. Verify MongoDB Atlas cluster is running")
        print("3. Check network connectivity and IP whitelist")
        print("4. Verify credentials in MongoDB URI")
        # Set to None but don't crash the module
        db = None
        clients_collection = None
        users_collection = None

def upload_to_cloudinary(file, client_id, doc_type):
    """Upload file to Cloudinary cloud storage"""
    try:
        if not CLOUDINARY_AVAILABLE:
            raise Exception("Cloudinary library not available")
        if not CLOUDINARY_ENABLED:
            raise Exception("Cloudinary not configured")
        
        # Reset file pointer to beginning
        file.seek(0)
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{doc_type}_{original_filename}"
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file,
            folder=f"tmis-business-guru/clients/{client_id}",
            public_id=unique_filename,
            resource_type="auto",  # Automatically detect file type (image, pdf, etc.)
            use_filename=True,
            unique_filename=True,
            overwrite=False,
            quality="auto",  # Automatic quality optimization
            fetch_format="auto"  # Automatic format optimization
        )
        
        print(f"📤 Document uploaded to Cloudinary: {doc_type} -> {result['public_id']}")
        print(f"🔗 Cloudinary URL: {result['secure_url']}")
        print(f"📊 File size: {result['bytes']} bytes, Format: {result['format']}")
        
        return {
            'url': result['secure_url'],
            'public_id': result['public_id'],
            'format': result['format'],
            'bytes': result['bytes'],
            'original_filename': original_filename,
            'storage_type': 'cloudinary',
            'created_at': result['created_at']
        }
        
    except Exception as e:
        print(f"❌ Error uploading to Cloudinary: {str(e)}")
        raise

def delete_from_cloudinary(public_id, resource_type="auto"):
    """Delete file from Cloudinary with enhanced resource type detection"""
    try:
        if not CLOUDINARY_AVAILABLE:
            print(f"⚠️ Cloudinary library not available - cannot delete {public_id}")
            return False
        if not CLOUDINARY_ENABLED:
            print(f"⚠️ Cloudinary not enabled - cannot delete {public_id}")
            return False
        
        print(f"🗑️ Attempting to delete from Cloudinary: {public_id}")
        
        # Try different resource types if auto doesn't work
        resource_types_to_try = ["auto", "image", "raw", "video"]
        
        for res_type in resource_types_to_try:
            try:
                result = cloudinary.uploader.destroy(public_id, resource_type=res_type)
                
                if result['result'] == 'ok':
                    print(f"✅ Successfully deleted from Cloudinary: {public_id} (type: {res_type})")
                    return True
                elif result['result'] == 'not found':
                    print(f"📄 File not found in Cloudinary: {public_id} (type: {res_type})")
                    continue
                else:
                    print(f"⚠️ Unexpected result for {public_id} (type: {res_type}): {result}")
                    continue
                    
            except Exception as type_error:
                print(f"❌ Error with resource type {res_type} for {public_id}: {str(type_error)}")
                continue
        
        print(f"❌ Failed to delete {public_id} with all resource types")
        return False
        
    except Exception as e:
        print(f"❌ Error deleting from Cloudinary: {str(e)}")
        return False

# Create Blueprint with API prefix
client_bp = Blueprint('client', __name__)

# CORS headers are handled by Flask-CORS in app.py - no need for manual headers here

def check_database_connection():
    """Check if database connection is available and working"""
    if db is None:
        return False, "Database connection not available"
    
    try:
        db.command("ping")
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database ping failed: {str(e)}"

def get_database_status():
    """Get comprehensive database status for debugging"""
    try:
        if db is None:
            return {
                'status': 'disconnected',
                'message': 'Database object is None',
                'collections_available': False
            }
        
        # Test connection
        db.command("ping")
        
        # Get collection stats
        collections = db.list_collection_names()
        client_count = clients_collection.count_documents({}) if clients_collection else 0
        user_count = users_collection.count_documents({}) if users_collection else 0
        
        return {
            'status': 'connected',
            'message': 'Database connection successful',
            'collections_available': True,
            'collections': collections,
            'stats': {
                'clients': client_count,
                'users': user_count
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Database error: {str(e)}',
            'collections_available': False
        }

def get_admin_name(admin_id):
    """Get admin name from user ID"""
    try:
        admin = users_collection.find_one({'_id': ObjectId(admin_id)})
        if admin:
            return admin.get('name', admin.get('email', 'Admin'))
        return 'Admin'
    except:
        return 'Admin'

def get_tmis_users():
    """Get all users with tmis.* email addresses"""
    try:
        tmis_users = list(users_collection.find({
            'email': {'$regex': '^tmis\\.', '$options': 'i'}
        }))
        return tmis_users
    except:
        return []

# Email sending function
def send_email(to_email, subject, body):
    """Send email notification"""
    try:
        import smtplib
        from email.mime.text import MimeText
        from email.mime.multipart import MIMEMultipart
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MimeText(body, 'plain'))
        
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

@client_bp.route('/clients', methods=['POST'])
@jwt_required()
def create_client():
    try:
        current_user_id = get_jwt_identity()
        
        # Get current user information
        current_user = None
        if db is not None:
            try:
                current_user = users_collection.find_one({'email': current_user_id})
            except Exception as e:
                print(f"Error fetching user: {e}")
                current_user = None
        
        user_email = current_user.get('email', current_user_id) if current_user else current_user_id
        is_tmis_user = user_email.startswith('tmis.') if user_email else False
        
        print(f"👤 User creating client: {user_email}")
        print(f"🏢 Is TMIS user: {is_tmis_user}")
        print(f"☁️ Cloudinary enabled: {CLOUDINARY_ENABLED}")
        
        # Get form data
        data = request.form.to_dict()
        files = request.files
        
        # Generate client ID for document organization
        client_id = str(ObjectId())
        
        # Handle file uploads - CLOUDINARY ONLY (no local storage)
        uploaded_files = {}
        
        # Check if Cloudinary is available - only if files are being uploaded
        has_files_to_upload = any(file and file.filename for file in files.values()) if files else False
        
        if has_files_to_upload and (not CLOUDINARY_AVAILABLE or not CLOUDINARY_ENABLED):
            return jsonify({
                'error': 'Document upload service unavailable. Cloudinary is required for document storage.',
                'details': 'Please contact administrator to enable Cloudinary service.'
            }), 503
        
        print(f"☁️ Using Cloudinary ONLY for document storage - no local files")
        print(f"📁 Processing {len(files)} files for client {client_id}")
        
        for field_name, file in files.items():
            if file and file.filename:
                print(f"📄 Processing file: {field_name} -> {file.filename}")
                
                try:
                    if is_tmis_user:
                        print(f"🏢 TMIS user - uploading {file.filename} to Cloudinary")
                    else:
                        print(f"👤 Regular user - uploading {file.filename} to Cloudinary")
                    
                    print(f"☁️ Uploading {file.filename} to Cloudinary...")
                    uploaded_file = upload_to_cloudinary(file, client_id, field_name)
                    uploaded_files[field_name] = uploaded_file
                    print(f"✅ Successfully uploaded {file.filename} to Cloudinary")
                    
                except Exception as e:
                    print(f"❌ Error uploading {file.filename} to Cloudinary: {str(e)}")
                    
                    # Retry once for all users
                    print(f"🔄 Retrying Cloudinary upload for {file.filename}")
                    try:
                        # Reset file pointer and try again
                        file.seek(0)
                        uploaded_file = upload_to_cloudinary(file, client_id, field_name)
                        uploaded_files[field_name] = uploaded_file
                        print(f"✅ Retry successful - uploaded {file.filename} to Cloudinary")
                    except Exception as retry_error:
                        print(f"❌ Retry failed for {file.filename}: {str(retry_error)}")
                        return jsonify({
                            'error': f'Failed to upload document: {file.filename}',
                            'details': 'Cloudinary upload failed after retry. Please try again later.'
                        }), 500
        
        # Extract information from documents (only if DocumentProcessor is available)
        extracted_data = {}
        if DOCUMENT_PROCESSOR_AVAILABLE and uploaded_files:
            try:
                document_processor = DocumentProcessor()
                extracted_data = document_processor.process_all_documents(uploaded_files)
            except Exception as e:
                print(f"Error processing documents: {str(e)}")
                # Continue without extracted data
                extracted_data = {}
        
        # Get form data
        data = request.form.to_dict()
        
        # Handle payment_gateways JSON parsing
        if 'payment_gateways' in data:
            try:
                data['payment_gateways'] = json.loads(data['payment_gateways']) if data['payment_gateways'] else []
                print(f"💾 Creating client with payment_gateways: {data['payment_gateways']}")
            except json.JSONDecodeError:
                data['payment_gateways'] = []
                print(f"⚠️ Failed to parse payment_gateways JSON during creation: {data.get('payment_gateways')}")
        
        # Ensure default payment gateways are set if not provided
        if 'payment_gateways' not in data or not data['payment_gateways']:
            data['payment_gateways'] = ['Cashfree', 'Easebuzz']
            print(f"💾 Setting default payment gateways for new client: {data['payment_gateways']}")
        
        # Ensure payment gateway status is initialized
        if 'payment_gateways_status' not in data or not data['payment_gateways_status']:
            data['payment_gateways_status'] = {
                'Cashfree': 'pending',
                'Easebuzz': 'pending'
            }
            print(f"💾 Setting default payment gateway status for new client: {data['payment_gateways_status']}")
        
        # Create client data
        client_data = {
            '_id': ObjectId(client_id),
            'created_by': current_user_id,
            'created_at': datetime.utcnow(),
            'status': 'pending',
            'documents': uploaded_files,
            **extracted_data,
            **data  # Form data should override extracted data
        }
        
        # Insert client into database
        result = clients_collection.insert_one(client_data)
        
        # Send WhatsApp notification for new client
        whatsapp_result = None
        if WHATSAPP_SERVICE_AVAILABLE and client_whatsapp_service:
            try:
                whatsapp_result = client_whatsapp_service.send_new_client_message(client_data)
                print(f"WhatsApp notification result: {whatsapp_result}")
            except Exception as e:
                print(f"Error sending WhatsApp notification: {str(e)}")
                whatsapp_result = {'success': False, 'error': str(e)}
        
        response_data = {
            'message': 'Client created successfully',
            'client_id': str(result.inserted_id),
            'extracted_data': extracted_data
        }
        
        # Add WhatsApp result to response if attempted
        if whatsapp_result is not None:
            response_data['whatsapp_sent'] = whatsapp_result['success']
            if not whatsapp_result['success']:
                response_data['whatsapp_error'] = whatsapp_result.get('error', 'Unknown error')
        
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"Error creating client: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/test', methods=['GET'])
def test_clients():
    return jsonify({
        'message': 'Client routes are working',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@client_bp.route('/clients/cloudinary-status', methods=['GET'])
@jwt_required()
def cloudinary_status():
    """Debug endpoint to check Cloudinary configuration"""
    current_user_id = get_jwt_identity()
    
    # Get current user information
    current_user = None
    if db is not None:
        try:
            current_user = users_collection.find_one({'email': current_user_id})
        except Exception as e:
            print(f"Error fetching user: {e}")
            current_user = None
    
    user_email = current_user.get('email', current_user_id) if current_user else current_user_id
    is_tmis_user = user_email.startswith('tmis.') if user_email else False
    
    return jsonify({
        'user_email': user_email,
        'is_tmis_user': is_tmis_user,
        'cloudinary_available': CLOUDINARY_AVAILABLE,
        'cloudinary_enabled': CLOUDINARY_ENABLED,
        'cloudinary_cloud_name': CLOUDINARY_CLOUD_NAME if CLOUDINARY_ENABLED else 'Not configured',
        'should_use_cloudinary': CLOUDINARY_ENABLED or (is_tmis_user and CLOUDINARY_AVAILABLE),
        'environment_variables': {
            'CLOUDINARY_ENABLED': os.getenv('CLOUDINARY_ENABLED'),
            'CLOUDINARY_CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
            'CLOUDINARY_API_KEY': os.getenv('CLOUDINARY_API_KEY')[:10] + '...' if os.getenv('CLOUDINARY_API_KEY') else None,
            'CLOUDINARY_API_SECRET': 'Set' if os.getenv('CLOUDINARY_API_SECRET') else 'Not set'
        },
        'upload_logic': {
            'all_users_use_cloudinary_when_enabled': True,
            'tmis_users_get_priority_even_if_disabled': True,
            'fallback_to_local_on_cloudinary_failure': True
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@client_bp.route('/clients/production-debug', methods=['GET'])
def production_debug():
    """Production debug endpoint - no JWT required for troubleshooting"""
    try:
        # Get database status
        db_status = get_database_status()
        
        # Get environment info
        env_info = {
            'FLASK_ENV': os.getenv('FLASK_ENV', 'Not set'),
            'MONGODB_URI': 'Set' if os.getenv('MONGODB_URI') else 'Not set',
            'JWT_SECRET_KEY': 'Set' if os.getenv('JWT_SECRET_KEY') else 'Not set',
            'CLOUDINARY_ENABLED': os.getenv('CLOUDINARY_ENABLED', 'Not set'),
            'SMTP_EMAIL': 'Set' if os.getenv('SMTP_EMAIL') else 'Not set'
        }
        
        # Get system info
        system_info = {
            'working_directory': os.getcwd(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'files_in_directory': [f for f in os.listdir('.') if f.endswith('.py')][:10]  # First 10 Python files
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Production debug endpoint working',
            'timestamp': datetime.utcnow().isoformat(),
            'database': db_status,
            'environment': env_info,
            'system': system_info,
            'blueprint_info': {
                'name': client_bp.name,
                'url_prefix': getattr(client_bp, 'url_prefix', 'None'),
                'routes_count': len(client_bp.deferred_functions)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Production debug failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@client_bp.route('/clients', methods=['GET'])
@jwt_required()
def get_clients():
    try:
        print("=== GET CLIENTS DEBUG ===")
        print("JWT required endpoint accessed")
        
        # Get JWT claims for debugging
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        user_role = claims.get('role', 'user')
        user_email = claims.get('email', current_user_id)
        
        print(f"User ID: {current_user_id}")
        print(f"User Role: {user_role}")
        print(f"User Email: {user_email}")
        
        # Check database connection first
        if db is None:
            print("Database connection not available")
            return jsonify({
                'error': 'Database connection failed', 
                'clients': [],
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
        
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        print(f"Claims: {claims}")
        print(f"User role: {user_role}")
        print(f"Current user ID: {current_user_id}")
        
        # Check if collections exist
        collections = db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Count total clients in database
        try:
            total_client_count = clients_collection.count_documents({})
            print(f"Total clients in database: {total_client_count}")
        except Exception as count_error:
            print(f"Error counting clients: {str(count_error)}")
            return jsonify({'error': 'Error accessing client data', 'clients': []}), 500
        
        # Admin can see all clients, users can see only their clients
        if user_role == 'admin':
            print("Admin user - fetching all clients")
            clients_cursor = clients_collection.find()
        else:
            print(f"Regular user - fetching clients for user ID: {current_user_id}")
            clients_cursor = clients_collection.find({'created_by': current_user_id})
        
        clients_list = []
        processed_count = 0
        error_count = 0
        
        for client in clients_cursor:
            try:
                processed_count += 1
                print(f"Processing client {processed_count}: {client.get('_id')}")
                
                # Get staff information for created_by
                if 'created_by' in client and client['created_by']:
                    try:
                        staff = users_collection.find_one({'_id': ObjectId(client['created_by'])})
                        if staff:
                            client['staff_name'] = staff['username']
                            client['staff_email'] = staff['email']
                            client['created_by_name'] = staff['username']
                        else:
                            print(f"Staff not found for created_by: {client['created_by']}")
                            client['staff_name'] = 'Unknown'
                            client['staff_email'] = 'Unknown'
                            client['created_by_name'] = 'Unknown'
                    except Exception as staff_error:
                        print(f"Error getting staff info: {str(staff_error)}")
                        client['staff_name'] = 'Unknown'
                        client['staff_email'] = 'Unknown'
                        client['created_by_name'] = 'Unknown'
                else:
                    client['staff_name'] = 'Unknown'
                    client['staff_email'] = 'Unknown'
                    client['created_by_name'] = 'Unknown'
                
                # Get staff information for updated_by if exists
                if 'updated_by' in client and client['updated_by']:
                    try:
                        updated_staff = users_collection.find_one({'_id': ObjectId(client['updated_by'])})
                        client['updated_by_name'] = updated_staff['username'] if updated_staff else 'Unknown'
                    except Exception as e:
                        client['updated_by_name'] = 'Unknown'
                
                # Convert ObjectId to string
                client['_id'] = str(client['_id'])
                
                # Log client data for debugging
                print(f"Client {processed_count} data: ID={client['_id']}, Name={client.get('legal_name', 'N/A')}, Status={client.get('status', 'N/A')}")
                
                clients_list.append(client)
                
            except Exception as e:
                error_count += 1
                print(f"Error processing client {processed_count}: {str(e)}")
                # Skip this client but continue with others
                continue
        
        print(f"=== PROCESSING SUMMARY ===")
        print(f"Total clients processed: {processed_count}")
        print(f"Clients successfully added to list: {len(clients_list)}")
        print(f"Errors encountered: {error_count}")
        
        if len(clients_list) == 0 and total_client_count > 0:
            print("WARNING: No clients returned but database has clients. Possible permission or data issue.")
        
        return jsonify({'clients': clients_list}), 200
        
    except Exception as e:
        print(f"CRITICAL ERROR in get_clients: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'clients': []}), 500

@client_bp.route('/clients/<client_id>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_client_requests(client_id):
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        return response
    
    # Handle actual requests
    if request.method == 'PUT':
        return update_client(client_id)
    elif request.method == 'GET':
        return get_client_details(client_id)
    elif request.method == 'DELETE':
        return delete_client(client_id)
    else:
        return jsonify({'error': 'Method not allowed'}), 405

def update_client(client_id):
    try:
        print(f"=== UPDATE CLIENT DEBUG ===")
        print(f"Client ID: {client_id}")
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Authorization header: {request.headers.get('Authorization', 'Missing')}")
        
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        user_email = claims.get('email', current_user_id)
        
        print(f"User ID: {current_user_id}")
        print(f"User Role: {user_role}")
        print(f"User Email: {user_email}")
        print(f"JWT Claims: {claims}")
        
        # Find the client first to check permissions
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        if not client:
            print(f"❌ Client not found: {client_id}")
            return jsonify({'error': 'Client not found'}), 404
        
        print(f"Client found - Created by: {client.get('created_by')}")
        print(f"Client name: {client.get('legal_name', client.get('user_name', 'Unknown'))}")
        
        data = request.get_json()
        status = data.get('status')
        feedback = data.get('feedback', '')
        comments = data.get('comments', '')
        
        print(f"Update data - Status: {status}, Feedback: {feedback}, Comments: {comments}")
        
        # Check permissions
        # Only admin can update status and feedback
        # Regular users can update comments on their own clients
        if (status is not None or feedback is not None) and user_role != 'admin':
            print(f"❌ Permission denied: Non-admin user trying to update status/feedback")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if regular user is trying to update someone else's client
        if user_role != 'admin' and client.get('created_by') != current_user_id:
            print(f"❌ Permission denied: User {current_user_id} cannot update client created by {client.get('created_by')}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Prepare update data
        update_fields = {
            'updated_at': datetime.utcnow(),
            'updated_by': current_user_id
        }
        
        # Only add fields that are provided and user has permission to update
        if status is not None and user_role == 'admin':
            update_fields['status'] = status
        if feedback is not None and user_role == 'admin':
            update_fields['feedback'] = feedback
        # Comments can be updated by both admin and regular users (if they own the client)
        if comments is not None:
            update_fields['comments'] = comments
        
        # Update client
        result = clients_collection.update_one(
            {'_id': ObjectId(client_id)},
            {'$set': update_fields}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get client data for notifications
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        # Prepare response with basic success message first
        response_data = {'message': 'Client updated successfully'}
        
        # Add WhatsApp notification info to response if it's a comment update
        if comments is not None:
            # Send WhatsApp notification immediately for comment updates to get instant feedback
            whatsapp_result = None
            if WHATSAPP_SERVICE_AVAILABLE and client_whatsapp_service:
                try:
                    # Get updated client data
                    updated_client = clients_collection.find_one({'_id': ObjectId(client_id)})
                    whatsapp_result = client_whatsapp_service.send_comment_notification(updated_client, comments)
                    logger.info(f"WhatsApp notification result for comment '{comments}': {whatsapp_result}")
                except Exception as e:
                    logger.error(f"Error sending WhatsApp notification for comment: {str(e)}")
                    whatsapp_result = {'success': False, 'error': str(e)}
            
            # Add specific WhatsApp status to response for frontend feedback
            if whatsapp_result:
                if whatsapp_result.get('success', False):
                    response_data['whatsapp_sent'] = True
                else:
                    response_data['whatsapp_sent'] = False
                    error_msg = whatsapp_result.get('error', '').lower()
                    if ('quota exceeded' in error_msg or 
                        'monthly quota has been exceeded' in error_msg or
                        whatsapp_result.get('status_code') == 466):
                        response_data['whatsapp_quota_exceeded'] = True
                    else:
                        response_data['whatsapp_error'] = whatsapp_result.get('error', 'Failed to send WhatsApp message')
            else:
                # Indicate that a WhatsApp notification was attempted
                response_data['whatsapp_notification'] = 'attempted'
        
        # Send notifications asynchronously to avoid blocking the response
        def send_notifications():
            try:
                import time
                time.sleep(0.1)  # Small delay to ensure response is sent first
                
                # Send WhatsApp notification for comment updates
                whatsapp_result = None
                if comments is not None and WHATSAPP_SERVICE_AVAILABLE and client_whatsapp_service:
                    try:
                        whatsapp_result = client_whatsapp_service.send_comment_notification(client, comments)
                        logger.info(f"WhatsApp notification result for comment '{comments}': {whatsapp_result}")
                    except Exception as e:
                        logger.error(f"Error sending WhatsApp notification for comment: {str(e)}")
                        whatsapp_result = {'success': False, 'error': str(e)}
                
                # Send comprehensive email notification using email service
                try:
                    admin_name = get_admin_name(current_user_id)
                    tmis_users = get_tmis_users()
                    
                    print(f"Sending email notification for client update:")
                    print(f"Admin: {admin_name}")
                    print(f"TMIS Users found: {len(tmis_users)}")
                    print(f"Client user_email: {client.get('user_email', 'None')}")
                    print(f"Client company_email: {client.get('company_email', 'None')}")
                    
                    # Send email notification to all relevant parties
                    if EMAIL_SERVICE_AVAILABLE and email_service:
                        email_sent = email_service.send_client_update_notification(
                            client_data=client,
                            admin_name=admin_name,
                            tmis_users=tmis_users,
                            update_type="status updated"
                        )
                        
                        if email_sent:
                            print("Email notification sent successfully")
                        else:
                            print("Failed to send email notification")
                    else:
                        print("Email service not available - skipping notification")
                        
                except Exception as e:
                    print(f"Error sending email notification: {str(e)}")
            except Exception as e:
                print(f"Error in async notifications: {str(e)}")
        
        # Start the notification sending in a separate thread if it's a comment update
        if comments is not None:
            import threading
            notification_thread = threading.Thread(target=send_notifications)
            notification_thread.daemon = True  # Daemon thread will not prevent app from exiting
            notification_thread.start()
        
        # Return response immediately
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"Error in update_client: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>', methods=['GET'])
@jwt_required()
def get_client_details(client_id):
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = get_jwt_identity()
        
        # Find the client
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Check permissions - admin can see all, users can see only their clients
        if user_role != 'admin' and client.get('created_by') != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get staff information
        staff = users_collection.find_one({'_id': ObjectId(client['created_by'])})
        client['staff_name'] = staff['username'] if staff else 'Unknown'
        client['staff_email'] = staff['email'] if staff else 'Unknown'
        
        # Convert ObjectId to string
        client['_id'] = str(client['_id'])
        
        # Debug payment gateways data
        print(f"🔍 Client {client_id} payment_gateways data:")
        print(f"   Type: {type(client.get('payment_gateways'))}")
        print(f"   Value: {client.get('payment_gateways')}")
        print(f"   Raw client keys: {list(client.keys())}")
        
        # Process document paths to be accessible
        if 'documents' in client:
            processed_documents = {}
            for doc_type, file_info in client['documents'].items():
                if isinstance(file_info, dict) and file_info.get('storage_type') == 'cloudinary':
                    # For Cloudinary files, provide direct access
                    processed_documents[doc_type] = {
                        'file_name': file_info.get('original_filename', 'Unknown'),
                        'file_size': file_info.get('bytes', 0),
                        'file_type': file_info.get('format', 'unknown'),
                        'storage_type': 'cloudinary',
                        'preview_url': file_info['url'],  # Direct Cloudinary URL for preview
                        'download_url': f'/api/clients/{client_id}/download/{doc_type}',  # Backend download endpoint
                        'direct_url': file_info['url'],  # Direct Cloudinary URL as fallback
                        'public_id': file_info.get('public_id', ''),
                        'is_image': file_info.get('format', '').lower() in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'],
                        'is_pdf': file_info.get('format', '').lower() == 'pdf'
                    }
                elif isinstance(file_info, str) and os.path.exists(file_info):
                    # For local files
                    file_stats = os.stat(file_info)
                    file_size = file_stats.st_size
                    file_name = os.path.basename(file_info)
                    file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
                    
                    processed_documents[doc_type] = {
                        'file_name': file_name,
                        'file_size': file_size,
                        'file_type': file_ext,
                        'storage_type': 'local',
                        'preview_url': f'/api/clients/{client_id}/download/{doc_type}',
                        'download_url': f'/api/clients/{client_id}/download/{doc_type}',
                        'direct_url': f'/api/clients/{client_id}/download/{doc_type}',
                        'is_image': file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'],
                        'is_pdf': file_ext == 'pdf'
                    }
                else:
                    # Handle missing or invalid files
                    processed_documents[doc_type] = {
                        'file_name': 'File not found',
                        'file_size': 0,
                        'file_type': 'unknown',
                        'storage_type': 'missing',
                        'preview_url': None,
                        'download_url': None,
                        'direct_url': None,
                        'is_image': False,
                        'is_pdf': False,
                        'error': 'File not found or invalid format'
                    }
            
            client['processed_documents'] = processed_documents
            
            # Also update the original documents for backward compatibility
            for doc_type, file_info in client['documents'].items():
                if isinstance(file_info, dict) and file_info.get('storage_type') == 'cloudinary':
                    # Replace the complex object with just the URL for simple access
                    client['documents'][doc_type] = file_info['url']
        
        return jsonify({'client': client}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>/update', methods=['PUT', 'OPTIONS'])
@jwt_required(optional=True)
def update_client_details(client_id):
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        origin = request.headers.get('Origin')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin,Cache-Control,Access-Control-Allow-Headers,Access-Control-Request-Method,Access-Control-Request-Headers')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH,HEAD')
        response.headers.add('Access-Control-Max-Age', '86400')
        return response
    
    # For PUT requests, require JWT
    if request.method == 'PUT':
        # Verify JWT token
        try:
            verify_jwt_in_request()
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    
    try:
        print(f"=== CLIENT UPDATE REQUEST ===")
        print(f"Client ID: {client_id}")
        print(f"Method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"Origin: {request.headers.get('Origin', 'No origin')}")
        
        # Check database connection first
        if db is None or clients_collection is None:
            print(f"❌ Database connection not available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Test database connection
        try:
            db.command("ping")
            print(f"✅ Database connection verified")
        except Exception as db_error:
            print(f"❌ Database ping failed: {str(db_error)}")
            return jsonify({'error': 'Database connection failed'}), 500
        
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = claims.get('sub')
        
        # Get current user information
        current_user = None
        if db is not None:
            try:
                current_user = users_collection.find_one({'email': current_user_id})
            except Exception as e:
                print(f"Error fetching user: {e}")
                current_user = None
        
        user_email = current_user.get('email', current_user_id) if current_user else current_user_id
        is_tmis_user = user_email.startswith('tmis.') if user_email else False
        
        print(f"👤 User updating client: {user_email}")
        print(f"🏢 Is TMIS user: {is_tmis_user}")
        print(f"☁️ Cloudinary enabled: {CLOUDINARY_ENABLED}")
        
        # Find the client
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Check permissions - admin can update all, users can update only their clients
        print(f"=== PERMISSION CHECK ===")
        print(f"User role: {user_role}")
        print(f"Current user ID: {current_user_id}")
        print(f"Client created by: {client.get('created_by')}")
        print(f"Is admin: {user_role == 'admin'}")
        print(f"Is owner: {client.get('created_by') == current_user_id}")
        
        if user_role != 'admin' and client.get('created_by') != current_user_id:
            print(f"❌ Permission denied: User {current_user_id} (role: {user_role}) cannot update client created by {client.get('created_by')}")
            return jsonify({'error': 'Unauthorized'}), 403
        
        print(f"✅ Permission granted for user {current_user_id} to update client {client_id}")
        
        # Handle form data with files
        if 'multipart/form-data' in request.content_type:
            data = request.form
            files = request.files
            
            # Create update data dictionary
            update_data = {}
            
            # Update text fields
            text_fields = [
                'legal_name', 'trade_name', 'user_name', 'user_email', 'email',
                'company_email', 'optional_mobile_number',
                'mobile_number', 'business_name', 'business_type', 'constitution_type',
                'gst_number', 'gst_status', 'business_pan', 'ie_code', 'website',
                'address', 'district', 'state', 'pincode', 'business_address',
                'bank_name', 'account_name', 'account_number', 'ifsc_code', 'account_type',
                'bank_type', 'new_current_account', 'gateway', 'loan_purpose',
                'repayment_period', 'existing_loans', 'registration_number',
                'gst_legal_name', 'gst_trade_name', 'business_pan_name', 
                'business_pan_date', 'owner_name', 'owner_dob', 'has_business_pan',
                'business_url', 'feedback', 'status', 'new_business_account',
                'transaction_months', 'loan_status', 'comments',
                # New bank details fields
                'new_bank_account_number', 'new_ifsc_code', 'new_account_name', 'new_bank_name',
                # Payment gateways fields
                'payment_gateways', 'payment_gateways_status'
            ]
            
            for field in text_fields:
                if field in data:
                    if field == 'payment_gateways':
                        # Parse payment_gateways from JSON string
                        try:
                            payment_gateways_data = json.loads(data[field]) if data[field] else []
                            update_data[field] = payment_gateways_data
                            print(f"💾 Saving payment_gateways: {payment_gateways_data}")
                        except json.JSONDecodeError:
                            # If it's not valid JSON, treat as empty array
                            update_data[field] = []
                            print(f"⚠️ Failed to parse payment_gateways JSON: {data[field]}")
                    elif field == 'payment_gateways_status':
                        # Parse payment_gateways_status from JSON string
                        try:
                            gateways_status_data = json.loads(data[field]) if data[field] else {}
                            update_data[field] = gateways_status_data
                            print(f"💾 Saving payment_gateways_status: {gateways_status_data}")
                        except json.JSONDecodeError:
                            # If it's not valid JSON, treat as empty object
                            update_data[field] = {}
                            print(f"⚠️ Failed to parse payment_gateways_status JSON: {data[field]}")
                    else:
                        update_data[field] = data[field]
                elif field == 'payment_gateways':
                    # If payment_gateways is not in the data, preserve existing values
                    # This prevents accidental clearing of payment gateways from non-gateway editing components
                    print(f"💾 Payment gateways not in update data - preserving existing values")
                    if field not in update_data and client.get('payment_gateways'):
                        update_data[field] = client['payment_gateways']
                elif field == 'payment_gateways_status':
                    # Similar preservation for payment gateway status  
                    print(f"💾 Payment gateways status not in update data - preserving existing values")
                    if field not in update_data and client.get('payment_gateways_status'):
                        update_data[field] = client['payment_gateways_status']
                elif field == 'loan_status':
                    # Preserve loan status if not explicitly updated
                    print(f"💾 Loan status not in update data - preserving existing values")
                    if field not in update_data and client.get('loan_status'):
                        update_data[field] = client['loan_status']
            
            # Handle partner fields for partnerships
            for i in range(10):
                partner_name_field = f'partner_name_{i}'
                partner_dob_field = f'partner_dob_{i}'
                
                if partner_name_field in data:
                    update_data[partner_name_field] = data[partner_name_field]
                if partner_dob_field in data:
                    update_data[partner_dob_field] = data[partner_dob_field]
            
            # Update numeric fields
            numeric_fields = [
                'number_of_partners', 'transaction_done_by_client', 'required_loan_amount',
                'monthly_income', 'total_credit_amount', 'average_monthly_balance'
            ]
            
            for field in numeric_fields:
                if field in data:
                    try:
                        update_data[field] = float(data[field])
                    except ValueError:
                        pass
            
            # Handle file uploads - CLOUDINARY ONLY (no local storage)
            documents = client.get('documents', {})
            
            # Check if Cloudinary is available for file uploads - only if files are being uploaded
            has_files_to_upload = any(file and file.filename for file in files.values()) if files else False
            
            if has_files_to_upload and (not CLOUDINARY_AVAILABLE or not CLOUDINARY_ENABLED):
                return jsonify({
                    'error': 'Document upload service unavailable. Cloudinary is required for document storage.',
                    'details': 'Please contact administrator to enable Cloudinary service.'
                }), 503
            
            print(f"☁️ Using Cloudinary ONLY for document storage - no local files")
            print(f"📁 Processing {len(files)} files for client update {client_id}")
            
            for key, file in files.items():
                if file and file.filename:
                    print(f"📄 Processing file: {key} -> {file.filename}")
                    
                    try:
                        if is_tmis_user:
                            print(f"🏢 TMIS user - uploading {file.filename} to Cloudinary")
                        else:
                            print(f"👤 Regular user - uploading {file.filename} to Cloudinary")
                        
                        print(f"☁️ Uploading {file.filename} to Cloudinary...")
                        uploaded_file = upload_to_cloudinary(file, client_id, key)
                        documents[key] = uploaded_file
                        print(f"✅ Successfully uploaded {file.filename} to Cloudinary")
                        
                    except Exception as e:
                        print(f"❌ Error uploading {file.filename} to Cloudinary: {str(e)}")
                        
                        # Retry once for all users
                        print(f"🔄 Retrying Cloudinary upload for {file.filename}")
                        try:
                            # Reset file pointer and try again
                            file.seek(0)
                            uploaded_file = upload_to_cloudinary(file, client_id, key)
                            documents[key] = uploaded_file
                            print(f"✅ Retry successful - uploaded {file.filename} to Cloudinary")
                        except Exception as retry_error:
                            print(f"❌ Retry failed for {file.filename}: {str(retry_error)}")
                            return jsonify({
                                'error': f'Failed to upload document: {file.filename}',
                                'details': 'Cloudinary upload failed after retry. Please try again later.'
                            }), 500
            
            if documents:
                update_data['documents'] = documents
            
            # Handle deleted documents
            if 'deleted_documents' in data:
                try:
                    deleted_docs = json.loads(data['deleted_documents'])
                    if deleted_docs and isinstance(deleted_docs, list):
                        # Remove deleted documents from the client's documents
                        current_documents = client.get('documents', {})
                        for doc_type in deleted_docs:
                            if doc_type in current_documents:
                                # Delete the physical file if it exists
                                file_path = current_documents[doc_type]
                                if isinstance(file_path, dict) and file_path.get('storage_type') == 'cloudinary':
                                    delete_from_cloudinary(file_path['public_id'])
                                elif os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                        print(f"Deleted file: {file_path}")
                                    except Exception as e:
                                        print(f"Error deleting file {file_path}: {str(e)}")
                                
                                # Remove from documents dictionary
                                del current_documents[doc_type]
                        
                        update_data['documents'] = current_documents
                        print(f"Processed deleted documents: {deleted_docs}")
                except json.JSONDecodeError:
                    print("Error parsing deleted_documents JSON")
                except Exception as e:
                    print(f"Error handling deleted documents: {str(e)}")
            
        else:
            # Handle JSON data
            data = request.get_json()
            update_data = data
        
        # Only preserve critical fields for JSON requests or when doing general edits
        # Skip preservation when fields are explicitly being updated (like from FormData)
        if request.content_type and 'multipart/form-data' not in request.content_type:
            # This is a JSON request, preserve fields that weren't included
            critical_fields = ['payment_gateways', 'payment_gateways_status', 'loan_status']
            for field in critical_fields:
                if field not in update_data and client.get(field) is not None:
                    update_data[field] = client[field]
                    print(f"💾 Preserved existing {field}: {client[field]}")
        
        # For FormData requests (like status updates), don't override fields that were explicitly set
        # The FormData processing above already handles preservation correctly
        
        # Ensure default payment gateways are set if not already present
        if 'payment_gateways' not in update_data and not client.get('payment_gateways'):
            update_data['payment_gateways'] = ['Cashfree', 'Easebuzz']
            print(f"💾 Setting default payment gateways: {update_data['payment_gateways']}")
        
        # Ensure payment gateway status is initialized for default gateways
        if 'payment_gateways_status' not in update_data and not client.get('payment_gateways_status'):
            update_data['payment_gateways_status'] = {
                'Cashfree': 'pending',
                'Easebuzz': 'pending'
            }
            print(f"💾 Setting default payment gateway status: {update_data['payment_gateways_status']}")
        
        # Add updated timestamp and updated_by
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = current_user_id
        
        # Update client
        # Get old client data before update for WhatsApp comparison
        old_client = None
        if WHATSAPP_SERVICE_AVAILABLE and client_whatsapp_service:
            old_client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        # Update client
        result = clients_collection.update_one(
            {'_id': ObjectId(client_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Client not found'}), 404
        
        # Send email notification if admin made changes (but NOT for comment-only updates)
        if user_role == 'admin':
            # Check if this is a comment-only update
            is_comment_only_update = (
                len(update_data) <= 3 and  # Only updated_at, updated_by, and comments
                'comments' in update_data and
                'updated_at' in update_data and
                'updated_by' in update_data
            )
            
            # Only send email for non-comment updates
            if not is_comment_only_update:
                # Get updated client data
                updated_client = clients_collection.find_one({'_id': ObjectId(client_id)})
                admin_name = get_admin_name(current_user_id)
                tmis_users = get_tmis_users()
                
                # Send email notification to all relevant parties
                if EMAIL_SERVICE_AVAILABLE and email_service:
                    email_service.send_client_update_notification(
                        client_data=updated_client,
                        admin_name=admin_name,
                        tmis_users=tmis_users,
                        update_type="updated"
                    )
                    print(f"📧 Email notification sent for client update (non-comment)")
                else:
                    print(f"📧 Email notification skipped - comment-only update")
        
        # Send WhatsApp notification for client update
        whatsapp_results = []
        if WHATSAPP_SERVICE_AVAILABLE and client_whatsapp_service:
            try:
                # Get updated client data
                updated_client = clients_collection.find_one({'_id': ObjectId(client_id)})
                
                # Send multiple WhatsApp messages for all changes
                updated_fields = list(update_data.keys())
                
                # Special handling for IE Code document uploads
                # Check if IE Code document was uploaded in this update
                if 'documents' in update_data:
                    current_documents = update_data.get('documents', {})
                    old_documents = old_client.get('documents', {}) if old_client else {}
                    
                    # If IE Code document is new, add it to updated_fields
                    if ('ie_code_document' in current_documents and current_documents['ie_code_document'] and
                        ('ie_code_document' not in old_documents or not old_documents['ie_code_document'])):
                        if 'ie_code' not in updated_fields:
                            updated_fields.append('ie_code')
                        print(f"IE Code document detected as newly uploaded for client {client_id}")
                
                # Pass old payment gateways status for comparison
                if old_client and 'payment_gateways_status' in update_data:
                    old_client['old_payment_gateways_status'] = old_client.get('payment_gateways_status', {})
                whatsapp_results = client_whatsapp_service.send_multiple_client_update_messages(
                    updated_client, updated_fields, old_client)
                    
                print(f"WhatsApp notification results: {whatsapp_results}")
            except Exception as e:
                print(f"Error sending WhatsApp notification: {str(e)}")
                whatsapp_results = [{'success': False, 'error': str(e)}]
        
        print(f"✅ Client update completed successfully")
        response_data = {
            'success': True,
            'message': 'Client updated successfully',
            'client_id': client_id,
            'updated_fields': list(update_data.keys())
        }
        
        # Add WhatsApp results to response if attempted
        if whatsapp_results:
            # Check if any message was sent successfully
            success_count = sum(1 for result in whatsapp_results if result.get('success', False))
            response_data['whatsapp_sent'] = success_count > 0
            
            # Check for quota exceeded errors
            quota_exceeded = False
            for result in whatsapp_results:
                if not result.get('success', True):
                    error_msg = result.get('error', '').lower()
                    if ('quota exceeded' in error_msg or 
                        'monthly quota has been exceeded' in error_msg or
                        result.get('status_code') == 466):
                        quota_exceeded = True
                        break
            
            response_data['whatsapp_quota_exceeded'] = quota_exceeded
            
            if success_count < len(whatsapp_results):
                # If some failed, include error from first failure
                for result in whatsapp_results:
                    if not result.get('success', True):
                        response_data['whatsapp_error'] = result.get('error', 'Some messages failed to send')
                        break
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Error in update_client_details: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>', methods=['DELETE'])
@jwt_required()
def delete_client(client_id):
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = claims.get('sub')
        
        # Find the client
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Check permissions - admin can delete all, users can delete only their clients
        if user_role != 'admin' and client.get('created_by') != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Delete all associated documents from file system and Cloudinary
        documents_deleted = 0
        documents_failed = 0
        cloudinary_deleted = 0
        local_deleted = 0
        
        if 'documents' in client and client['documents']:
            print(f"🗑️ Deleting {len(client['documents'])} documents for client {client_id}...")
            
            for doc_type, file_info in client['documents'].items():
                print(f"📄 Processing document: {doc_type}")
                
                # Handle new format (dict with metadata)
                if isinstance(file_info, dict):
                    if file_info.get('storage_type') == 'cloudinary' and file_info.get('public_id'):
                        print(f"☁️ Deleting Cloudinary document: {doc_type} -> {file_info['public_id']}")
                        if delete_from_cloudinary(file_info['public_id']):
                            documents_deleted += 1
                            cloudinary_deleted += 1
                            print(f"✅ Successfully deleted Cloudinary document: {doc_type}")
                        else:
                            documents_failed += 1
                            print(f"❌ Failed to delete Cloudinary document: {doc_type}")
                    elif file_info.get('storage_type') == 'local' and file_info.get('url'):
                        local_path = file_info['url']
                        if os.path.exists(local_path):
                            try:
                                os.remove(local_path)
                                documents_deleted += 1
                                local_deleted += 1
                                print(f"✅ Successfully deleted local document: {doc_type} -> {local_path}")
                            except Exception as e:
                                documents_failed += 1
                                print(f"❌ Failed to delete local document {doc_type} ({local_path}): {str(e)}")
                        else:
                            print(f"⚠️ Local file not found: {local_path}")
                
                # Handle old format (direct file path string)
                elif isinstance(file_info, str):
                    if os.path.exists(file_info):
                        try:
                            os.remove(file_info)
                            documents_deleted += 1
                            local_deleted += 1
                            print(f"✅ Successfully deleted legacy document: {doc_type} -> {file_info}")
                        except Exception as e:
                            documents_failed += 1
                            print(f"❌ Failed to delete legacy document {doc_type} ({file_info}): {str(e)}")
                    else:
                        print(f"⚠️ Legacy file not found: {file_info}")
                
                else:
                    print(f"⚠️ Unknown document format for {doc_type}: {type(file_info)}")
            
            print(f"📊 Document deletion summary:")
            print(f"   ☁️ Cloudinary documents deleted: {cloudinary_deleted}")
            print(f"   💾 Local documents deleted: {local_deleted}")
            print(f"   ❌ Failed deletions: {documents_failed}")
            print(f"   ✅ Total successful: {documents_deleted}")
        
        # Try to delete the client's upload directory if it exists
        try:
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], client_id)
            if os.path.exists(upload_path):
                import shutil
                shutil.rmtree(upload_path)
                print(f"Successfully deleted client upload directory: {upload_path}")
        except Exception as e:
            print(f"Failed to delete client upload directory: {str(e)}")
        
        # Delete client record from database
        result = clients_collection.delete_one({'_id': ObjectId(client_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Client not found'}), 404
        
        # Log deletion summary
        client_name = client.get('legal_name') or client.get('user_name') or 'Unknown'
        print(f"=== CLIENT DELETION SUMMARY ===")
        print(f"Client ID: {client_id}")
        print(f"Client Name: {client_name}")
        print(f"Documents deleted: {documents_deleted}")
        print(f"Documents failed: {documents_failed}")
        print(f"Database record deleted: {result.deleted_count > 0}")
        print(f"Deleted by: {current_user_id} (Role: {user_role})")
        
        return jsonify({
            'message': 'Client and all associated documents deleted successfully',
            'client_id': client_id,
            'client_name': client_name,
            'deletion_summary': {
                'total_documents_deleted': documents_deleted,
                'cloudinary_documents_deleted': cloudinary_deleted,
                'local_documents_deleted': local_deleted,
                'failed_deletions': documents_failed,
                'database_record_deleted': True
            }
        }), 200
        
    except Exception as e:
        print(f"Error deleting client {client_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>/download/<document_type>')
@jwt_required()
def download_document(client_id, document_type):
    try:
        from flask import redirect, Response
        import requests
        from io import BytesIO
        
        print(f"🔍 Download request: client_id={client_id}, document_type={document_type}")
        
        # Check database connection
        if clients_collection is None:
            print(f"❌ Database connection not available")
            return jsonify({'error': 'Database service unavailable'}), 503
        
        # Validate client_id format
        try:
            ObjectId(client_id)
        except Exception as e:
            print(f"❌ Invalid client_id format: {client_id}")
            return jsonify({'error': 'Invalid client ID format'}), 400
        
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            print(f"❌ Client not found: {client_id}")
            return jsonify({'error': 'Client not found'}), 404
        
        print(f"✅ Client found: {client.get('legal_name', client.get('user_name', 'Unknown'))}")
        
        # Check if documents exist
        if 'documents' not in client or not client['documents']:
            print(f"❌ No documents found for client: {client_id}")
            return jsonify({'error': 'No documents available for this client'}), 404
        
        print(f"📄 Available documents: {list(client['documents'].keys())}")
        
        if document_type not in client.get('documents', {}):
            print(f"❌ Document type not found: {document_type}")
            return jsonify({'error': 'Document type not found'}), 404
        
        document_info = client['documents'][document_type]
        
        if isinstance(document_info, dict):
            if document_info.get('storage_type') == 'cloudinary':
                cloudinary_url = document_info['url']
                print(f"🔗 Redirecting to Cloudinary URL: {cloudinary_url}")
                return redirect(cloudinary_url)
            elif document_info.get('storage_type') == 'local':
                local_path = document_info['url']
                if os.path.exists(local_path):
                    print(f"💾 Sending local file: {local_path}")
                    return send_file(local_path, as_attachment=True)
                else:
                    print(f"⚠️ Local file not found: {local_path}")
                    return jsonify({'error': 'Local file not found'}), 404
            else:
                print(f"⚠️ Unknown storage type: {document_info.get('storage_type')}")
                return jsonify({'error': 'Unknown storage type'}), 400
        elif isinstance(document_info, str):
            if os.path.exists(document_info):
                print(f"💾 Sending legacy document: {document_info}")
                return send_file(document_info, as_attachment=True)
            else:
                print(f"⚠️ Legacy file not found: {document_info}")
                return jsonify({'error': 'Legacy file not found'}), 404
        else:
            print(f"⚠️ Unknown document format: {type(document_info)}")
            return jsonify({'error': 'Unknown document format'}), 400
        
    except Exception as e:
        print(f"Error downloading document: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/extract-gst-data', methods=['POST'])
@jwt_required()
def extract_gst_data_direct():
    """Extract data from GST document directly without creating a client"""
    try:
        print(f"=== DIRECT GST DATA EXTRACTION REQUEST ===")
        
        # Check if DocumentProcessor is available
        if not DOCUMENT_PROCESSOR_AVAILABLE or DocumentProcessor is None:
            return jsonify({'error': 'Document processing service not available'}), 503
        
        # Check if file was uploaded
        if 'gst_document' not in request.files:
            return jsonify({'error': 'No GST document uploaded'}), 400
        
        file = request.files['gst_document']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid GST document'}), 400
        
        # Create temporary file for processing
        import tempfile
        import os
        
        # Save uploaded file to temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        gst_file_path = temp_file.name
        print(f"💾 Saved uploaded GST document to temporary file: {gst_file_path}")
        
        # Process the GST document
        try:
            document_processor = DocumentProcessor()
            extracted_data = document_processor.extract_gst_info(gst_file_path)
            print(f"✅ Extracted GST data: {extracted_data}")
            
            # Clean up temporary file
            try:
                os.unlink(gst_file_path)
                print(f"🧹 Cleaned up temporary file: {gst_file_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temporary file: {e}")
            
            return jsonify({
                'success': True,
                'extracted_data': extracted_data
            }), 200
            
        except Exception as e:
            # Clean up temporary file
            try:
                os.unlink(gst_file_path)
                print(f"🧹 Cleaned up temporary file after error: {gst_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to clean up temporary file after error: {cleanup_error}")
            
            print(f"❌ Error processing GST document: {str(e)}")
            return jsonify({'error': f'Failed to process GST document: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ Error in direct GST data extraction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/extract-gst-data', methods=['POST'])
@jwt_required()
def extract_gst_data_direct():
    """Extract data from GST document directly without creating a client"""
    try:
        print(f"=== DIRECT GST DATA EXTRACTION REQUEST ===")
        
        # Check if DocumentProcessor is available
        if not DOCUMENT_PROCESSOR_AVAILABLE or DocumentProcessor is None:
            return jsonify({'error': 'Document processing service not available'}), 503
        
        # Check if file was uploaded
        if 'gst_document' not in request.files:
            return jsonify({'error': 'No GST document uploaded'}), 400
        
        file = request.files['gst_document']
        if not file or not file.filename:
            return jsonify({'error': 'Invalid GST document'}), 400
        
        # Create temporary file for processing
        import tempfile
        import os
        
        # Save uploaded file to temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        file.save(temp_file.name)
        temp_file.close()
        
        gst_file_path = temp_file.name
        print(f"💾 Saved uploaded GST document to temporary file: {gst_file_path}")
        
        # Process the GST document
        try:
            document_processor = DocumentProcessor()
            extracted_data = document_processor.extract_gst_info(gst_file_path)
            print(f"✅ Extracted GST data: {extracted_data}")
            
            # Clean up temporary file
            try:
                os.unlink(gst_file_path)
                print(f"🧹 Cleaned up temporary file: {gst_file_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temporary file: {e}")
            
            return jsonify({
                'success': True,
                'extracted_data': extracted_data
            }), 200
            
        except Exception as e:
            # Clean up temporary file
            try:
                os.unlink(gst_file_path)
                print(f"🧹 Cleaned up temporary file after error: {gst_file_path}")
            except Exception as cleanup_error:
                print(f"⚠️ Failed to clean up temporary file after error: {cleanup_error}")
            
            print(f"❌ Error processing GST document: {str(e)}")
            return jsonify({'error': f'Failed to process GST document: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ Error in direct GST data extraction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>/extract-gst-data', methods=['POST'])
@jwt_required()
def extract_gst_data(client_id):
    """Extract data from GST document and return extracted information"""
    try:
        print(f"=== EXTRACT GST DATA REQUEST ===")
        print(f"Client ID: {client_id}")
        
        # Check database connection
        if db is None or clients_collection is None:
            print(f"❌ Database connection not available")
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Find the client
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Check if GST document exists
        documents = client.get('documents', {})
        if 'gst_document' not in documents:
            return jsonify({'error': 'GST document not found'}), 404
        
        gst_document_info = documents['gst_document']
        
        # Check if DocumentProcessor is available
        if not DOCUMENT_PROCESSOR_AVAILABLE or DocumentProcessor is None:
            return jsonify({'error': 'Document processing service not available'}), 503
        
        # Create temporary file path for processing
        # For Cloudinary documents, we need to download them first
        if isinstance(gst_document_info, dict) and gst_document_info.get('storage_type') == 'cloudinary':
            import requests
            import tempfile
            import os
            
            cloudinary_url = gst_document_info['url']
            print(f"📥 Downloading GST document from Cloudinary: {cloudinary_url}")
            
            # Download the file
            response = requests.get(cloudinary_url)
            if response.status_code != 200:
                return jsonify({'error': 'Failed to download GST document'}), 500
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file.close()
            
            gst_file_path = temp_file.name
            print(f"💾 Saved GST document to temporary file: {gst_file_path}")
        else:
            # For local files
            gst_file_path = gst_document_info
        
        # Process the GST document
        try:
            document_processor = DocumentProcessor()
            extracted_data = document_processor.extract_gst_info(gst_file_path)
            print(f"✅ Extracted GST data: {extracted_data}")
            
            # Clean up temporary file if it was created
            if isinstance(gst_document_info, dict) and gst_document_info.get('storage_type') == 'cloudinary':
                try:
                    os.unlink(gst_file_path)
                    print(f"🧹 Cleaned up temporary file: {gst_file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to clean up temporary file: {e}")
            
            return jsonify({
                'success': True,
                'extracted_data': extracted_data
            }), 200
            
        except Exception as e:
            # Clean up temporary file if it was created
            if isinstance(gst_document_info, dict) and gst_document_info.get('storage_type') == 'cloudinary':
                try:
                    os.unlink(gst_file_path)
                    print(f"🧹 Cleaned up temporary file after error: {gst_file_path}")
                except Exception as cleanup_error:
                    print(f"⚠️ Failed to clean up temporary file after error: {cleanup_error}")
            
            print(f"❌ Error processing GST document: {str(e)}")
            return jsonify({'error': f'Failed to process GST document: {str(e)}'}), 500
        
    except Exception as e:
        print(f"❌ Error in extract_gst_data: {str(e)}")
        return jsonify({'error': str(e)}), 500
        print(f"❌ Error in extract_gst_data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@client_bp.route('/clients/<client_id>/download/<document_type>')
@jwt_required()
def download_document(client_id, document_type):
    try:
        from flask import redirect, Response
        import requests
        from io import BytesIO
        
        print(f"🔍 Download request: client_id={client_id}, document_type={document_type}")
        # Validate Cloudinary URL
        if not cloudinary_url or not cloudinary_url.startswith('https://'):
            print(f"❌ Invalid Cloudinary URL: {cloudinary_url}")
            return jsonify({'error': 'Invalid document URL'}), 500
        
        # Download file from Cloudinary
        print(f"📥 Downloading from Cloudinary: {cloudinary_url}")
        cloudinary_response = requests.get(cloudinary_url, timeout=30, stream=True)
        
        print(f"📊 Cloudinary response status: {cloudinary_response.status_code}")
        print(f"📊 Cloudinary response headers: {dict(cloudinary_response.headers)}")
        
        cloudinary_response.raise_for_status()
        
        # Get the file content
        file_content = cloudinary_response.content
        print(f"📦 Downloaded content size: {len(file_content)} bytes")
        
        # Determine the correct mimetype
        file_format = file_info.get('format', '').lower()
        if file_format == 'pdf':
            mimetype = 'application/pdf'
        elif file_format in ['jpg', 'jpeg']:
            mimetype = 'image/jpeg'
        elif file_format == 'png':
            mimetype = 'image/png'
        elif file_format == 'gif':
            mimetype = 'image/gif'
        elif file_format == 'webp':
            mimetype = 'image/webp'
        else:
            mimetype = 'application/octet-stream'
        
        print(f"✅ Successfully downloaded {original_filename} ({len(file_content)} bytes)")
        print(f"📄 File format: {file_format}, MIME type: {mimetype}")
        
        # Log PDF info but don't validate signature (trust Cloudinary)
        if file_format == 'pdf':
            print(f"📄 PDF file detected: {original_filename}")
            print(f"Content type from Cloudinary: {cloudinary_response.headers.get('content-type', 'unknown')}")
            print(f"File size: {len(file_content)} bytes")
            # Trust Cloudinary's file format - no signature validation needed
        
        # Create proper Flask response with enhanced headers for PDF
        response_headers = {
            'Content-Disposition': f'attachment; filename="{original_filename}"',
            'Content-Length': str(len(file_content)),
            'Content-Type': mimetype,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Content-Type-Options': 'nosniff',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        }
        
        # Additional headers for PDF files
        if file_format == 'pdf':
            response_headers.update({
                'Content-Transfer-Encoding': 'binary',
                'Accept-Ranges': 'bytes',
                'X-Frame-Options': 'SAMEORIGIN'
            })
        
        flask_response = Response(
            file_content,
            mimetype=mimetype,
            headers=response_headers
        )
        
        return flask_response
        
            except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading from Cloudinary: {str(e)}")
        print(f"❌ Request exception type: {type(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"❌ Response status: {e.response.status_code}")
            print(f"❌ Response text: {e.response.text[:500]}")
        # Fallback: redirect to Cloudinary URL
        return redirect(cloudinary_url)
            except Exception as e:
        print(f"❌ Error processing Cloudinary file: {str(e)}")
        print(f"❌ Exception type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
        
        # Handle string URLs (direct Cloudinary URLs)
        elif isinstance(file_info, str) and file_info.startswith('https://res.cloudinary.com'):
            try:
        print(f"📥 Downloading from Cloudinary URL: {file_info}")
        cloudinary_response = requests.get(file_info, timeout=30, stream=True)
        cloudinary_response.raise_for_status()
        
        # Extract filename from URL or use document type
        filename = f'{document_type}.{file_info.split(".")[-1] if "." in file_info else "bin"}'
        
        # Get the file content
        file_content = cloudinary_response.content
        
        # Determine mimetype from URL extension
        if file_info.lower().endswith('.pdf'):
            mimetype = 'application/pdf'
        elif file_info.lower().endswith(('.jpg', '.jpeg')):
            mimetype = 'image/jpeg'
        elif file_info.lower().endswith('.png'):
            mimetype = 'image/png'
        elif file_info.lower().endswith('.gif'):
            mimetype = 'image/gif'
        elif file_info.lower().endswith('.webp'):
            mimetype = 'image/webp'
        else:
            mimetype = 'application/octet-stream'
        
        print(f"✅ Successfully downloaded {filename} ({len(file_content)} bytes)")
        print(f"📄 MIME type: {mimetype}")
        
        # Log PDF info but don't validate signature (trust Cloudinary)
        if mimetype == 'application/pdf':
                    print(f"📄 PDF file detected from URL")
                    print(f"Content type from Cloudinary: {cloudinary_response.headers.get('content-type', 'unknown')}")
                    print(f"File size: {len(file_content)} bytes")
                    # Trust Cloudinary's file format - no signature validation needed
                
                # Create proper Flask response with enhanced headers
                response_headers = {
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Length': str(len(file_content)),
                    'Content-Type': mimetype,
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'X-Content-Type-Options': 'nosniff',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                }
                
                # Additional headers for PDF files
                if mimetype == 'application/pdf':
                    response_headers.update({
                        'Content-Transfer-Encoding': 'binary',
                        'Accept-Ranges': 'bytes',
                        'X-Frame-Options': 'SAMEORIGIN'
                    })
                
                flask_response = Response(
                    file_content,
                    mimetype=mimetype,
                    headers=response_headers
                )
                
                return flask_response
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error downloading from Cloudinary URL: {str(e)}")
                # Fallback: redirect to the URL
                return redirect(file_info)
            except Exception as e:
                print(f"❌ Error processing Cloudinary URL: {str(e)}")
                return jsonify({'error': f'Failed to download file: {str(e)}'}), 500
        
        # Handle local files
        elif isinstance(file_info, str) and os.path.exists(file_info):
            return send_file(file_info, as_attachment=True)
        else:
            return jsonify({'error': 'File not found on server'}), 404
        
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        print(f"❌ Exception type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Provide more specific error messages
        error_message = str(e)
        if 'ObjectId' in error_message:
            error_message = 'Invalid client ID format'
        elif 'not found' in error_message.lower():
            error_message = 'Document or client not found'
        elif 'cloudinary' in error_message.lower():
            error_message = 'Document storage service error'
        elif 'timeout' in error_message.lower():
            error_message = 'Request timeout - please try again'
        
        return jsonify({
            'error': error_message,
            'details': f'Download failed for document type: {document_type}',
            'client_id': client_id,
            'document_type': document_type
        }), 500

@client_bp.route('/clients/<client_id>/preview/<document_type>')
@jwt_required()
def preview_document(client_id, document_type):
    """Preview endpoint that serves files for inline viewing (not download)"""
    try:
        from flask import redirect, Response
        import requests
        
        print(f"🔍 Preview request: client_id={client_id}, document_type={document_type}")
        
        # Check database connection
        if clients_collection is None:
            print(f"❌ Database connection not available for preview")
            return jsonify({'error': 'Database service unavailable'}), 503
        
        # Validate client_id format
        try:
            ObjectId(client_id)
        except Exception as e:
            print(f"❌ Invalid client_id format for preview: {client_id}")
            return jsonify({'error': 'Invalid client ID format'}), 400
        
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            print(f"❌ Client not found for preview: {client_id}")
            return jsonify({'error': 'Client not found'}), 404
        
        print(f"✅ Client found for preview: {client.get('legal_name', client.get('user_name', 'Unknown'))}")
        
        # Check if documents exist
        if 'documents' not in client or not client['documents']:
            print(f"❌ No documents found for preview: {client_id}")
            return jsonify({'error': 'No documents available for this client'}), 404
        
        print(f"📄 Available documents for preview: {list(client['documents'].keys())}")
        
        if document_type not in client.get('documents', {}):
            print(f"❌ Document type '{document_type}' not found for preview. Available: {list(client['documents'].keys())}")
            return jsonify({'error': f'Document type "{document_type}" not found'}), 404
        
        file_info = client['documents'][document_type]
        print(f"📋 File info for preview {document_type}: {type(file_info)} - {str(file_info)[:200]}...")
        
        # Handle Cloudinary files - serve the content directly for better compatibility
        if isinstance(file_info, dict) and file_info.get('storage_type') == 'cloudinary':
            cloudinary_url = file_info['url']
            original_filename = file_info.get('original_filename', f'{document_type}.{file_info.get("format", "bin")}')
            
            try:
                print(f"📥 Fetching for preview from Cloudinary: {cloudinary_url}")
                cloudinary_response = requests.get(cloudinary_url, timeout=30, stream=True)
                cloudinary_response.raise_for_status()
                
                # Get the file content
                file_content = cloudinary_response.content
                
                # Determine the correct mimetype
                file_format = file_info.get('format', '').lower()
                if file_format == 'pdf':
                    mimetype = 'application/pdf'
                elif file_format in ['jpg', 'jpeg']:
                    mimetype = 'image/jpeg'
                elif file_format == 'png':
                    mimetype = 'image/png'
                elif file_format == 'gif':
                    mimetype = 'image/gif'
                elif file_format == 'webp':
                    mimetype = 'image/webp'
                else:
                    mimetype = 'application/octet-stream'
                
                print(f"✅ Successfully fetched for preview: {original_filename} ({len(file_content)} bytes)")
                print(f"📄 File format: {file_format}, MIME type: {mimetype}")
                
                # Create proper Flask response for inline viewing (not download)
                response_headers = {
                    'Content-Type': mimetype,
                    'Content-Length': str(len(file_content)),
                    'Cache-Control': 'public, max-age=3600',  # Allow caching for preview
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                }
                
                # For inline viewing, don't set Content-Disposition as attachment
                if mimetype in ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                    response_headers['Content-Disposition'] = f'inline; filename="{original_filename}"'
                else:
                    response_headers['Content-Disposition'] = f'attachment; filename="{original_filename}"'
                
                flask_response = Response(
                    file_content,
                    mimetype=mimetype,
                    headers=response_headers
                )
                
                return flask_response
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching from Cloudinary for preview: {str(e)}")
                # Fallback: redirect to Cloudinary URL
                return redirect(cloudinary_url)
            except Exception as e:
                print(f"❌ Error processing Cloudinary file for preview: {str(e)}")
                return jsonify({'error': f'Failed to preview file: {str(e)}'}), 500
        
        # Handle string URLs (direct Cloudinary URLs)
        elif isinstance(file_info, str) and file_info.startswith('https://res.cloudinary.com'):
            try:
                print(f"📥 Fetching for preview from Cloudinary URL: {file_info}")
                cloudinary_response = requests.get(file_info, timeout=30, stream=True)
                cloudinary_response.raise_for_status()
                
                # Extract filename from URL or use document type
                filename = f'{document_type}.{file_info.split(".")[-1] if "." in file_info else "bin"}'
                
                # Get the file content
                file_content = cloudinary_response.content
                
                # Determine mimetype from URL extension
                if file_info.lower().endswith('.pdf'):
                    mimetype = 'application/pdf'
                elif file_info.lower().endswith(('.jpg', '.jpeg')):
                    mimetype = 'image/jpeg'
                elif file_info.lower().endswith('.png'):
                    mimetype = 'image/png'
                elif file_info.lower().endswith('.gif'):
                    mimetype = 'image/gif'
                elif file_info.lower().endswith('.webp'):
                    mimetype = 'image/webp'
                else:
                    mimetype = 'application/octet-stream'
                
                print(f"✅ Successfully fetched for preview: {filename} ({len(file_content)} bytes)")
                print(f"📄 MIME type: {mimetype}")
                
                # Create proper Flask response for inline viewing
                response_headers = {
                    'Content-Type': mimetype,
                    'Content-Length': str(len(file_content)),
                    'Cache-Control': 'public, max-age=3600',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
                }
                
                # For inline viewing
                if mimetype in ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                    response_headers['Content-Disposition'] = f'inline; filename="{filename}"'
                else:
                    response_headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                flask_response = Response(
                    file_content,
                    mimetype=mimetype,
                    headers=response_headers
                )
                
                return flask_response
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching from Cloudinary URL for preview: {str(e)}")
                # Fallback: redirect to the URL
                return redirect(file_info)
            except Exception as e:
                print(f"❌ Error processing Cloudinary URL for preview: {str(e)}")
                return jsonify({'error': f'Failed to preview file: {str(e)}'}), 500
        
        # Handle local files
        elif isinstance(file_info, str) and os.path.exists(file_info):
            # Determine mimetype for inline viewing
            file_ext = os.path.splitext(file_info)[1].lower()
            if file_ext == '.pdf':
                mimetype = 'application/pdf'
            elif file_ext in ['.jpg', '.jpeg']:
                mimetype = 'image/jpeg'
            elif file_ext == '.png':
                mimetype = 'image/png'
            elif file_ext == '.gif':
                mimetype = 'image/gif'
            elif file_ext == '.webp':
                mimetype = 'image/webp'
            else:
                mimetype = 'application/octet-stream'
            
            return send_file(file_info, mimetype=mimetype)
        else:
            return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        print(f"❌ Preview error: {str(e)}")
        print(f"❌ Exception type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        
        # Provide more specific error messages
        error_message = str(e)
        if 'ObjectId' in error_message:
            error_message = 'Invalid client ID format'
        elif 'not found' in error_message.lower():
            error_message = 'Document or client not found'
        elif 'cloudinary' in error_message.lower():
            error_message = 'Document storage service error'
        elif 'timeout' in error_message.lower():
            error_message = 'Request timeout - please try again'
        
        return jsonify({
            'error': error_message,
            'details': f'Preview failed for document type: {document_type}',
            'client_id': client_id,
            'document_type': document_type
        }), 500

@client_bp.route('/clients/<client_id>/download-direct/<document_type>')
@jwt_required()
def download_document_direct(client_id, document_type):
    """
    Direct download endpoint that simply redirects to Cloudinary URL for maximum compatibility
    """
    try:
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        if document_type not in client.get('documents', {}):
            return jsonify({'error': 'Document not found'}), 404
        
        file_info = client['documents'][document_type]
        
        # Handle Cloudinary files - direct redirect to Cloudinary URL
        if isinstance(file_info, dict) and file_info.get('storage_type') == 'cloudinary':
            cloudinary_url = file_info['url']
            print(f"📥 Direct redirect to Cloudinary: {cloudinary_url}")
            return redirect(cloudinary_url)
        
        # Handle string URLs (direct Cloudinary URLs)
        elif isinstance(file_info, str) and file_info.startswith('https://res.cloudinary.com'):
            print(f"📥 Direct redirect to Cloudinary URL: {file_info}")
            return redirect(file_info)
        
        # Handle local files
        elif isinstance(file_info, str) and os.path.exists(file_info):
            return send_file(file_info, as_attachment=True)
        else:
            return jsonify({'error': 'File not found on server'}), 404
        
    except Exception as e:
        print(f"❌ Direct download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>/download-raw/<document_type>')
@jwt_required()
def download_document_raw(client_id, document_type):
    """
    Raw download endpoint that serves the file exactly as stored in Cloudinary
    """
    try:
        from flask import Response
        import requests
        
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        if document_type not in client.get('documents', {}):
            return jsonify({'error': 'Document not found'}), 404
        
        file_info = client['documents'][document_type]
        
        # Handle Cloudinary files - raw download
        if isinstance(file_info, dict) and file_info.get('storage_type') == 'cloudinary':
            cloudinary_url = file_info['url']
            original_filename = file_info.get('original_filename', f'{document_type}.{file_info.get("format", "bin")}')
            
            try:
                print(f"📥 Raw download from Cloudinary: {cloudinary_url}")
                
                # Use requests.get with stream=True to avoid loading entire file into memory
                with requests.get(cloudinary_url, timeout=30, stream=True) as cloudinary_response:
                    cloudinary_response.raise_for_status()
                    
                    # Get content type from Cloudinary response
                    content_type = cloudinary_response.headers.get('content-type', 'application/octet-stream')
                    content_length = cloudinary_response.headers.get('content-length')
                    
                    print(f"📄 Content-Type from Cloudinary: {content_type}")
                    print(f"📏 Content-Length: {content_length}")
                    
                    # Create a generator to stream the content
                    def generate():
                        for chunk in cloudinary_response.iter_content(chunk_size=8192):
                            if chunk:
                                yield chunk
                    
                    # Create response with headers that preserve the original file
                    response_headers = {
                        'Content-Disposition': f'attachment; filename="{original_filename}"',
                        'Content-Type': content_type,
                    }
                    
                    if content_length:
                        response_headers['Content-Length'] = content_length
                    
                    flask_response = Response(
                        generate(),
                        mimetype=content_type,
                        headers=response_headers
                    )
                    
                    print(f"✅ Raw download initiated: {original_filename}")
                    return flask_response
                
            except Exception as e:
                print(f"❌ Error in raw download: {str(e)}")
                # Fallback: redirect to Cloudinary URL
                from flask import redirect
                return redirect(cloudinary_url)
        
        # Handle string URLs (direct Cloudinary URLs)
        elif isinstance(file_info, str) and file_info.startswith('https://res.cloudinary.com'):
            from flask import redirect
            return redirect(file_info)
        
        # Handle local files
        elif isinstance(file_info, str) and os.path.exists(file_info):
            return send_file(file_info, as_attachment=True)
        else:
            return jsonify({'error': 'File not found on server'}), 404
        
    except Exception as e:
        print(f"❌ Raw download error: {str(e)}")
        return jsonify({'error': str(e)}), 500
