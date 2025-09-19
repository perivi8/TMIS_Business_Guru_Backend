from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from bson import ObjectId
from bson.json_util import dumps
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from email_service import email_service
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Try to import DocumentProcessor, but make it optional
try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    print("Warning: DocumentProcessor not available. Document processing will be skipped.")
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DocumentProcessor = None

# Load environment variables
load_dotenv()

# Cloudinary configuration
CLOUDINARY_ENABLED = os.getenv('CLOUDINARY_ENABLED', 'false').lower() == 'true'
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

# Initialize Cloudinary if enabled
if CLOUDINARY_ENABLED and CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
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
    print("⚠️ Cloudinary credentials not found or incomplete")
    CLOUDINARY_ENABLED = False

# MongoDB connection for this module with error handling
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    print("❌ CRITICAL ERROR: MONGODB_URI environment variable not found in client_routes!")
    raise Exception("MONGODB_URI environment variable is required")

print(f"🔄 Client routes connecting to MongoDB...")
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
    raise Exception(f"Failed to connect to MongoDB in client_routes: {str(e)}")

def upload_to_cloudinary(file, client_id, doc_type):
    """Upload file to Cloudinary cloud storage"""
    try:
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
    """Delete file from Cloudinary"""
    try:
        if not CLOUDINARY_ENABLED:
            return False
        
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        success = result['result'] == 'ok'
        
        if success:
            print(f"🗑️ Document deleted from Cloudinary: {public_id}")
        else:
            print(f"⚠️ Failed to delete from Cloudinary: {public_id} - {result}")
            
        return success
        
    except Exception as e:
        print(f"❌ Error deleting from Cloudinary: {str(e)}")
        return False

client_bp = Blueprint('client', __name__)

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

@client_bp.route('/api/clients', methods=['POST'])
@jwt_required()
def create_client():
    try:
        current_user_id = get_jwt_identity()
        
        # Get form data
        data = request.form.to_dict()
        files = request.files
        
        # Create uploads directory for this client
        client_id = str(ObjectId())
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], client_id)
        os.makedirs(upload_path, exist_ok=True)
        
        # Handle file uploads
        uploaded_files = {}
        
        # Process each uploaded file
        for field_name, file in files.items():
            if file and file.filename:
                if CLOUDINARY_ENABLED:
                    try:
                        uploaded_file = upload_to_cloudinary(file, client_id, field_name)
                        uploaded_files[field_name] = uploaded_file
                    except Exception as e:
                        print(f"Error uploading to Cloudinary: {str(e)}")
                else:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(upload_path, filename)
                    file.save(file_path)
                    uploaded_files[field_name] = file_path
        
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

@client_bp.route('/api/clients/test', methods=['GET'])
def test_clients():
    """Test endpoint to check database without authentication"""
    try:
        # Check database connection
        db_stats = db.command("dbstats")
        collections = db.list_collection_names()
        
        # Count clients
        client_count = clients_collection.count_documents({})
        
        # Get sample client if exists
        sample_client = clients_collection.find_one()
        
        return jsonify({
            'database_connected': True,
            'collections': collections,
            'client_count': client_count,
            'sample_client_id': str(sample_client['_id']) if sample_client else None,
            'sample_client_keys': list(sample_client.keys()) if sample_client else None
        }), 200
        
    except Exception as e:
        return jsonify({
            'database_connected': False,
            'error': str(e)
        }), 500

@client_bp.route('/api/clients', methods=['GET'])
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

@client_bp.route('/api/clients/<client_id>', methods=['GET'])
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
                        'download_url': f'/api/clients/{client_id}/download/{doc_type}'
                    }
            client['processed_documents'] = processed_documents
        
        return jsonify({'client': client}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/api/clients/<client_id>', methods=['PUT'])
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
                
        except Exception as e:
            print(f"Error sending email notification: {str(e)}")
        
        return jsonify({'message': 'Client updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/api/clients/<client_id>/update', methods=['PUT'])
@jwt_required()
def update_client_details(client_id):
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        current_user_id = claims.get('sub')
        
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
            
            # Handle file uploads
            documents = client.get('documents', {})
            
            for key, file in files.items():
                if file and file.filename:
                    if CLOUDINARY_ENABLED:
                        try:
                            uploaded_file = upload_to_cloudinary(file, client_id, key)
                            documents[key] = uploaded_file
                        except Exception as e:
                            print(f"Error uploading to Cloudinary: {str(e)}")
                    else:
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{client_id}_{filename}")
                        file.save(file_path)
                        documents[key] = file_path
            
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
            email_service.send_client_update_notification(
                client_data=updated_client,
                admin_name=admin_name,
                tmis_users=tmis_users,
                update_type="updated"
            )
        
        return jsonify({'message': 'Client updated successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@client_bp.route('/api/clients/<client_id>', methods=['DELETE'])
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
        
        # Delete all associated documents from file system
        documents_deleted = 0
        documents_failed = 0
        
        if 'documents' in client and client['documents']:
            print(f"Deleting documents for client {client_id}...")
            
            for doc_type, file_path in client['documents'].items():
                if isinstance(file_path, dict) and file_path.get('storage_type') == 'cloudinary':
                    if delete_from_cloudinary(file_path['public_id']):
                        documents_deleted += 1
                        print(f"Successfully deleted document from Cloudinary: {doc_type} -> {file_path['public_id']}")
                    else:
                        documents_failed += 1
                        print(f"Failed to delete document from Cloudinary: {doc_type} -> {file_path['public_id']}")
                elif os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        documents_deleted += 1
                        print(f"Successfully deleted document: {doc_type} -> {file_path}")
                    except Exception as e:
                        documents_failed += 1
                        print(f"Failed to delete document {doc_type} ({file_path}): {str(e)}")
        
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
            'client_name': client_name,
            'documents_deleted': documents_deleted,
            'documents_failed': documents_failed
        }), 200
        
    except Exception as e:
        print(f"Error deleting client {client_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@client_bp.route('/api/clients/<client_id>/download/<document_type>')
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
