from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
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
    print("🔧 Using fallback MongoDB URI for this deployment...")
    MONGODB_URI = "mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0"

print(f"🔄 Client routes connecting to MongoDB...")
print(f"MongoDB URI: {MONGODB_URI[:50]}...{MONGODB_URI[-20:]}")  # Hide credentials in logs

try:
    client = MongoClient(MONGODB_URI)
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
    if db is None or clients_collection is None or users_collection is None:
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
        if users_collection:
            current_user = users_collection.find_one({'email': current_user_id})
        
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
        
        # Check if Cloudinary is available
        if not CLOUDINARY_AVAILABLE or not CLOUDINARY_ENABLED:
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
        
        return jsonify({
            'message': 'Client created successfully',
            'client_id': str(result.inserted_id),
            'extracted_data': extracted_data
        }), 201
        
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
    if users_collection:
        current_user = users_collection.find_one({'email': current_user_id})
    
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
        
        # Check database connection first
        if db is None or clients_collection is None or users_collection is None:
            print("Database connection not available")
            return jsonify({'error': 'Database connection failed', 'clients': []}), 500
        
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
        
        # Process document paths to be accessible
        if 'documents' in client:
            processed_documents = {}
            for doc_type, file_path in client['documents'].items():
                if isinstance(file_path, dict) and file_path.get('storage_type') == 'cloudinary':
                    processed_documents[doc_type] = {
                        'file_name': file_path['original_filename'],
                        'file_size': file_path['bytes'],
                        'file_path': file_path['url'],
                        'download_url': file_path['url']
                    }
                elif os.path.exists(file_path):
                    # Get file info
                    file_stats = os.stat(file_path)
                    file_size = file_stats.st_size
                    file_name = os.path.basename(file_path)
                    
                    processed_documents[doc_type] = {
                        'file_name': file_name,
                        'file_size': file_size,
                        'file_path': file_path,
                        'download_url': f'/clients/{client_id}/download/{doc_type}'
                    }
            client['processed_documents'] = processed_documents
        
        return jsonify({'client': client}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>', methods=['PUT'])
@jwt_required()
def update_client(client_id):
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        
        # Only admin can update client status and feedback
        if user_role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        status = data.get('status')
        feedback = data.get('feedback', '')
        
        # Update client
        current_user_id = get_jwt_identity()
        result = clients_collection.update_one(
            {'_id': ObjectId(client_id)},
            {
                '$set': {
                    'status': status,
                    'feedback': feedback,
                    'updated_at': datetime.utcnow(),
                    'updated_by': current_user_id
                }
            }
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Client not found'}), 404
        
        # Get client data for email notification
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
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
        
        return jsonify({'message': 'Client updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/clients/<client_id>/update', methods=['PUT'])
@jwt_required()
def update_client_details(client_id):
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = claims.get('sub')
        
        # Get current user information
        current_user = None
        if users_collection:
            current_user = users_collection.find_one({'email': current_user_id})
        
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
        if user_role != 'admin' and client.get('created_by') != current_user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
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
                'bank_name', 'account_number', 'ifsc_code', 'account_type',
                'bank_type', 'new_current_account', 'gateway', 'loan_purpose',
                'repayment_period', 'existing_loans', 'registration_number',
                'gst_legal_name', 'gst_trade_name', 'business_pan_name', 
                'business_pan_date', 'owner_name', 'owner_dob', 'has_business_pan',
                'business_url', 'feedback', 'status', 'new_business_account',
                'transaction_months'
            ]
            
            for field in text_fields:
                if field in data:
                    update_data[field] = data[field]
            
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
            
            # Check if Cloudinary is available for file uploads
            if files and (not CLOUDINARY_AVAILABLE or not CLOUDINARY_ENABLED):
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
        
        # Add updated timestamp and updated_by
        update_data['updated_at'] = datetime.utcnow()
        update_data['updated_by'] = current_user_id
        
        # Update client
        result = clients_collection.update_one(
            {'_id': ObjectId(client_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Client not found'}), 404
        
        # Send email notification if admin made changes
        if user_role == 'admin':
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
        
        return jsonify({'message': 'Client updated successfully'}), 200
        
    except Exception as e:
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
        client = clients_collection.find_one({'_id': ObjectId(client_id)})
        
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        if document_type not in client.get('documents', {}):
            return jsonify({'error': 'Document not found'}), 404
        
        file_path = client['documents'][document_type]
        
        if isinstance(file_path, dict) and file_path.get('storage_type') == 'cloudinary':
            return jsonify({'url': file_path['url']}), 200
        elif not os.path.exists(file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
