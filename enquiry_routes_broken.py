from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import GreenAPI WhatsApp service (with corrected endpoint)
whatsapp_service = None
try:
    from greenapi_whatsapp_service import whatsapp_service
    logger.info(f"✅ GreenAPI WhatsApp service imported: {whatsapp_service is not None}")
    if whatsapp_service and getattr(whatsapp_service, 'api_available', False):
        logger.info(f"   ✅ GreenAPI service is available and ready")
        logger.info(f"   🔗 Using endpoint: {getattr(whatsapp_service, 'base_url', 'Unknown')}")
        
        # Test connection immediately
        try:
            status = whatsapp_service.check_status()
            if status.get('connected'):
                logger.info(f"   🎉 GreenAPI connection successful! State: {status.get('state')}")
            else:
                logger.warning(f"   ⚠️ GreenAPI not connected: {status.get('error')}")
        except Exception as status_error:
            logger.warning(f"   ⚠️ GreenAPI status check failed: {status_error}")
    else:
        logger.warning(f"   ⚠️ GreenAPI service not available")
        whatsapp_service = None
except Exception as import_error:
    logger.error(f"❌ Failed to import GreenAPI service: {import_error}")
    whatsapp_service = None

# Log final service status
if whatsapp_service is None:
    logger.error(f"❌ No WhatsApp service available - WhatsApp features will be disabled")
else:
    service_type = "GreenAPI" if hasattr(whatsapp_service, 'base_url') else "Unknown"
    logger.info(f"✅ WhatsApp service ready: {service_type}")

# Create Blueprint
enquiry_bp = Blueprint('enquiry', __name__)

# MongoDB Atlas connection using existing .env configuration
try:
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        logger.error("MONGODB_URI not found in environment variables")
        raise ValueError("MONGODB_URI environment variable is required")
    
    logger.info(f"Connecting to MongoDB Atlas...")
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)  # 5 second timeout
    
    # Test connection
    client.admin.command('ping')
    logger.info("MongoDB Atlas connection successful")
    
    # Use the same database as client_routes
    db = client.tmis_business_guru
    
    # Create collections
    enquiries_collection = db.enquiries
    users_collection = db.users
    
    # Create indexes for better performance
    try:
        enquiries_collection.create_index("mobile_number")
        enquiries_collection.create_index("date")
        enquiries_collection.create_index("staff")
        logger.info("Created indexes for enquiries collection")
    except Exception as index_error:
        logger.warning(f"Index creation warning: {index_error}")
    
    logger.info("Enquiry routes connected to MongoDB Atlas successfully")
    
except Exception as e:
    logger.error(f"MongoDB Atlas connection failed: {e}")
    logger.warning("Setting database collections to None - enquiry routes will return errors")
    # Don't raise exception, just set collections to None
    db = None
    enquiries_collection = None
    users_collection = None

def serialize_enquiry(enquiry):
    """Convert MongoDB document to JSON serializable format"""
    if enquiry:
        if '_id' in enquiry and isinstance(enquiry['_id'], ObjectId):
            enquiry['_id'] = str(enquiry['_id'])
        if 'date' in enquiry and isinstance(enquiry['date'], datetime):
            enquiry['date'] = enquiry['date'].isoformat()
        if 'created_at' in enquiry and isinstance(enquiry['created_at'], datetime):
            enquiry['created_at'] = enquiry['created_at'].isoformat()
        if 'updated_at' in enquiry and isinstance(enquiry['updated_at'], datetime):
            enquiry['updated_at'] = enquiry['updated_at'].isoformat()
    return enquiry

def parse_date_safely(date_input):
    """Safely parse date input with multiple fallback options"""
    try:
        if isinstance(date_input, str):
            # Try different date formats
            date_formats = [
                '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds and Z
                '%Y-%m-%dT%H:%M:%SZ',     # ISO format with Z
                '%Y-%m-%dT%H:%M:%S',      # ISO format without Z
                '%Y-%m-%d'                # Date only
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
            
            # Try fromisoformat as last resort
            try:
                return datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        elif isinstance(date_input, datetime):
            return date_input
        
        # If all parsing fails, return current datetime
        logger.warning(f"Could not parse date: {date_input}, using current datetime")
        return datetime.now()
        
    except Exception as e:
        logger.error(f"Error parsing date {date_input}: {e}")
        return datetime.now()

@enquiry_bp.route('/enquiries/test', methods=['GET'])
def test_connection():
    """Test endpoint to check database connectivity"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({
            'status': 'error',
            'message': 'Database not available'
        }), 500
    
    try:
        # Test database connection
        client.admin.command('ping')
        
        # Count documents in enquiries collection
        count = enquiries_collection.count_documents({})
        
        return jsonify({
            'status': 'success',
            'message': 'MongoDB Atlas connection successful',
            'storage_type': 'mongodb_atlas',
            'enquiries_count': count,
            'database': db.name,
            'collections': db.list_collection_names()
        }), 200
        
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Database test failed: {str(e)}'
        }), 500

@enquiry_bp.route('/enquiries', methods=['GET'])
@jwt_required()
def get_all_enquiries():
    """Get all enquiries"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} requesting all enquiries")
        
        # Get all enquiries sorted by date (newest first)
        enquiries = list(enquiries_collection.find().sort('date', -1))
        
        # Serialize enquiries
        serialized_enquiries = [serialize_enquiry(enquiry) for enquiry in enquiries]
        
        logger.info(f"Retrieved {len(serialized_enquiries)} enquiries")
        return jsonify(serialized_enquiries), 200
        
    except Exception as e:
        logger.error(f"Error retrieving enquiries: {e}")
        return jsonify({'error': 'Failed to retrieve enquiries'}), 500

@enquiry_bp.route('/enquiries/<enquiry_id>', methods=['GET'])
@jwt_required()
def get_enquiry_by_id(enquiry_id):
    """Get a specific enquiry by ID"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} requesting enquiry {enquiry_id}")
        
        # Validate ObjectId
        if not ObjectId.is_valid(enquiry_id):
            return jsonify({'error': 'Invalid enquiry ID'}), 400
        
        enquiry = enquiries_collection.find_one({'_id': ObjectId(enquiry_id)})
        
        if not enquiry:
            return jsonify({'error': 'Enquiry not found'}), 404
        
        serialized_enquiry = serialize_enquiry(enquiry)
        return jsonify(serialized_enquiry), 200
        
    except Exception as e:
        logger.error(f"Error retrieving enquiry {enquiry_id}: {e}")
        return jsonify({'error': 'Failed to retrieve enquiry'}), 500

@enquiry_bp.route('/enquiries/public', methods=['POST'])
def create_public_enquiry():
    """Create a new public enquiry without authentication"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        # Get JSON data with error handling
        data = request.get_json(force=True)
        
        logger.info(f"Received public enquiry creation request: {data}")
        
        if not data:
            logger.error("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['wati_name', 'mobile_number']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(f"{field} (not present)")
            elif not str(data[field]).strip():
                missing_fields.append(f"{field} (empty)")
        
        if missing_fields:
            error_msg = f"Missing or empty required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Validate mobile number format
        mobile_number = str(data.get('mobile_number', '')).strip()
        logger.info(f"Validating mobile number: '{mobile_number}'")
        
        if not mobile_number:
            logger.error("Mobile number is empty")
            return jsonify({'error': 'Mobile number is required'}), 400
        
        if not mobile_number.isdigit():
            logger.error(f"Mobile number contains non-digits: '{mobile_number}'")
            return jsonify({'error': 'Mobile number must contain only digits'}), 400
            
        # Accept mobile numbers with country codes (10-15 digits)
        if len(mobile_number) < 10 or len(mobile_number) > 15:
            logger.error(f"Mobile number length is {len(mobile_number)}, expected 10-15 digits: '{mobile_number}'")
            return jsonify({'error': f'Mobile number must be 10-15 digits (with country code), got {len(mobile_number)}'}), 400
        
        # Validate other required fields
        wati_name = str(data.get('wati_name', '')).strip()
        # Don't set default staff to 'Public Enquiry', leave it empty so staff can be manually assigned
        staff = str(data.get('staff', '')).strip()  # Changed from 'Public Enquiry' to empty string
        comments = str(data.get('comments', 'New Public Enquiry')).strip()
        business_nature = str(data.get('business_nature', '')).strip()
        
        logger.info(f"Wati name: '{wati_name}', Staff: '{staff}', Comments: '{comments}', Business Nature: '{business_nature}'")
        
        if not wati_name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Create enquiry document
        enquiry_data = {
            'wati_name': wati_name,
            'user_name': wati_name,  # Use the same name for user_name
            'mobile_number': mobile_number,
            'secondary_mobile_number': data.get('secondary_mobile_number'),  # Use the validated variable
            'gst': data.get('gst', ''),  # Default to empty string
            'gst_status': '',  # Default to empty
            'business_type': '',  # Default to empty
            'business_nature': business_nature,  # Save business name in business_nature column
            'staff': staff,  # Leave empty instead of 'Public Enquiry'
            'comments': comments,
            'additional_comments': '',
            'date': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
            # Remove 'staff_locked': False - no longer needed since we allow staff reassignment
        }
        
        logger.info(f"Final public enquiry document to insert: {enquiry_data}")
        
        # Insert enquiry into MongoDB Atlas
        result = enquiries_collection.insert_one(enquiry_data)
        
        # Retrieve the created enquiry
        created_enquiry = enquiries_collection.find_one({'_id': result.inserted_id})
        serialized_enquiry = serialize_enquiry(created_enquiry)
        
        # Send WhatsApp welcome message for public enquiries
        try:
            if whatsapp_service is not None:
                logger.info(f"Attempting to send WhatsApp welcome message to {mobile_number}")
                
                # Determine message type based on comment for new public enquiries
                message_type = whatsapp_service.get_comment_message_type(comments)
                logger.info(f"Determined message type for new public enquiry: {message_type}")
                
                whatsapp_result = whatsapp_service.send_enquiry_message(
                    enquiry_data, 
                    message_type=message_type
                )
                
                if whatsapp_result['success']:
                    logger.info(f"WhatsApp welcome message sent successfully to {mobile_number}")
                    serialized_enquiry['whatsapp_sent'] = True
                    serialized_enquiry['whatsapp_message_id'] = whatsapp_result.get('message_id')
                    serialized_enquiry['whatsapp_message_type'] = message_type
                    serialized_enquiry['whatsapp_error'] = None
                    # Add notification
                    serialized_enquiry['whatsapp_notification'] = whatsapp_result.get('notification', 'WhatsApp message sent successfully')
                else:
                    error_msg = whatsapp_result.get('error', 'Unknown error')
                    solution = whatsapp_result.get('solution', '')
                    status_code = whatsapp_result.get('status_code')
                    
                    logger.warning(f"Failed to send WhatsApp message: {error_msg}")
                    
                    # Provide more specific error messages for common issues
                    user_friendly_error = "WhatsApp message failed to send"
                    
                    if status_code == 466:
                        user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                    elif "quota exceeded" in error_msg.lower():
                        user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                    elif "unauthorized" in error_msg.lower() or status_code == 401:
                        user_friendly_error = "GreenAPI authentication failed - Check API credentials"
                    elif "forbidden" in error_msg.lower() or status_code == 403:
                        user_friendly_error = "GreenAPI access forbidden - Check API permissions"
                    elif "bad request" in error_msg.lower() or status_code == 400:
                        user_friendly_error = "Invalid phone number format or WhatsApp not available for this number"
                    elif "not found" in error_msg.lower() or status_code == 404:
                        user_friendly_error = "GreenAPI endpoint not found - Check API configuration"
                    elif "network error" in error_msg.lower():
                        user_friendly_error = "Network connection error - Check internet connectivity"
                    else:
                        # For other errors, show the original error message
                        user_friendly_error = error_msg
                    
                    serialized_enquiry['whatsapp_sent'] = False
                    serialized_enquiry['whatsapp_error'] = user_friendly_error
                    
                    # Add notification for quota exceeded
                    if status_code == 466 or "quota exceeded" in error_msg.lower():
                        serialized_enquiry['whatsapp_notification'] = "⚠️ GreenAPI monthly quota exceeded. Please upgrade your GreenAPI plan to send messages to more numbers."
                    
                    # Also include the original error for debugging
                    if solution:
                        serialized_enquiry['whatsapp_debug_error'] = f"{error_msg}. Solution: {solution}"
                    else:
                        serialized_enquiry['whatsapp_debug_error'] = error_msg
            else:
                logger.error("WhatsApp service is not initialized")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "WhatsApp service not available - Check GreenAPI configuration"
                
        except Exception as whatsapp_error:
            logger.error(f"WhatsApp service error: {str(whatsapp_error)}")
            serialized_enquiry['whatsapp_sent'] = False
            serialized_enquiry['whatsapp_error'] = str(whatsapp_error)
        
        logger.info(f"Successfully created public enquiry {result.inserted_id}")
        return jsonify(serialized_enquiry), 201
        
    except Exception as e:
        logger.error(f"Error creating public enquiry: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@enquiry_bp.route('/enquiries/public', methods=['POST'])
@enquiry_bp.route('/enquiries', methods=['POST'])
@jwt_required()
def create_enquiry():
    """Create a new enquiry"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        logger.info(f"Received enquiry creation request from user: {current_user}")
        logger.info(f"Request data: {data}")
        
        if not data:
            logger.error("No data provided in request")
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"User {current_user} creating new enquiry with data: {data}")
        
        # Validate required fields with detailed error messages
        required_fields = ['wati_name', 'mobile_number', 'staff', 'comments']
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(f"{field} (not present)")
            elif not str(data[field]).strip():
                missing_fields.append(f"{field} (empty)")
        
        if missing_fields:
            error_msg = f"Missing or empty required fields: {', '.join(missing_fields)}"
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        # Validate mobile number format
        mobile_number = str(data.get('mobile_number', '')).strip()
        logger.info(f"Validating mobile number: '{mobile_number}'")
        
        if not mobile_number:
            logger.error("Mobile number is empty")
            return jsonify({'error': 'Mobile number is required'}), 400
        
        if not mobile_number.isdigit():
            logger.error(f"Mobile number contains non-digits: '{mobile_number}'")
            return jsonify({'error': 'Mobile number must contain only digits'}), 400
            
        # Accept mobile numbers with country codes (10-15 digits)
        if len(mobile_number) < 10 or len(mobile_number) > 15:
            logger.error(f"Mobile number length is {len(mobile_number)}, expected 10-15 digits: '{mobile_number}'")
            return jsonify({'error': f'Mobile number must be 10-15 digits (with country code), got {len(mobile_number)}'}), 400
        
        # Validate secondary mobile number if provided
        secondary_mobile = data.get('secondary_mobile_number')
        if secondary_mobile is not None and secondary_mobile != '':
            secondary_mobile = str(secondary_mobile).strip()
            logger.info(f"Validating secondary mobile number: '{secondary_mobile}'")
            if not secondary_mobile.isdigit():
                logger.error(f"Secondary mobile number contains non-digits: '{secondary_mobile}'")
                return jsonify({'error': 'Secondary mobile number must contain only digits'}), 400
            # Accept secondary mobile numbers with country codes (10-15 digits)
            if len(secondary_mobile) < 10 or len(secondary_mobile) > 15:
                logger.error(f"Secondary mobile number length is {len(secondary_mobile)}, expected 10-15 digits: '{secondary_mobile}'")
                return jsonify({'error': f'Secondary mobile number must be 10-15 digits (with country code), got {len(secondary_mobile)}'}), 400
        else:
            logger.info("Secondary mobile number is null/empty - skipping validation")
            secondary_mobile = None  # Ensure it's None for database storage
        
        # Validate GST and GST status
        gst_value = str(data.get('gst', '')).strip()
        logger.info(f"GST value: '{gst_value}'")
        
        # Allow empty GST value (will be displayed as "Not Selected" in frontend)
        if gst_value and gst_value not in ['Yes', 'No']:
            logger.error(f"Invalid GST value: '{gst_value}', must be 'Yes' or 'No'")
            return jsonify({'error': 'GST must be either "Yes" or "No"'}), 400
        
        if gst_value == 'Yes':
            gst_status = str(data.get('gst_status', '')).strip()
            logger.info(f"GST status when GST=Yes: '{gst_status}'")
            if not gst_status:
                logger.error("GST status required when GST is Yes")
                return jsonify({'error': 'GST status is required when GST is Yes'}), 400
        
        # Validate other required fields
        wati_name = str(data.get('wati_name', '')).strip()
        staff = str(data.get('staff', '')).strip()
        comments = str(data.get('comments', '')).strip()
        
        logger.info(f"Wati name: '{wati_name}', Staff: '{staff}', Comments: '{comments}'")
        
        if not wati_name:
            return jsonify({'error': 'Wati name is required'}), 400
        if not staff:
            return jsonify({'error': 'Staff is required'}), 400
        if not comments:
            return jsonify({'error': 'Comments is required'}), 400
        
        # Parse date safely
        parsed_date = parse_date_safely(data.get('date'))
        logger.info(f"Parsed date: {parsed_date}")
        
        # Create enquiry document
        # Set default GST value to empty string if not provided
        gst_for_db = gst_value if gst_value in ['Yes', 'No'] else ''
        
        enquiry_data = {
            'wati_name': data.get('wati_name'),
            'user_name': data.get('user_name'),
            'mobile_number': mobile_number,
            'secondary_mobile_number': secondary_mobile,  # Use the validated variable
            'gst': gst_for_db,
            'gst_status': data.get('gst_status', ''),
            'business_type': data.get('business_type'),
            'business_nature': data.get('business_nature'),
            'staff': data.get('staff'),
            'comments': data.get('comments'),
            'additional_comments': data.get('additional_comments', ''),
            'date': parsed_date,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
            # Remove 'staff_locked': False - no longer needed since we allow staff reassignment
        }
        
        logger.info(f"Final enquiry document to insert: {enquiry_data}")
        
        # Insert enquiry into MongoDB Atlas
        result = enquiries_collection.insert_one(enquiry_data)
        
        # Retrieve the created enquiry
        created_enquiry = enquiries_collection.find_one({'_id': result.inserted_id})
        serialized_enquiry = serialize_enquiry(created_enquiry)
        
        # Send WhatsApp welcome message
        try:
            if whatsapp_service is not None:
                logger.info(f"Attempting to send WhatsApp welcome message to {mobile_number}")
                
                # Determine message type based on comment for new enquiries as well
                message_type = whatsapp_service.get_comment_message_type(data.get('comments', ''))
                logger.info(f"Determined message type for new enquiry: {message_type}")
                
                whatsapp_result = whatsapp_service.send_enquiry_message(
                    enquiry_data, 
                    message_type=message_type
                )
                
                if whatsapp_result['success']:
                    logger.info(f"WhatsApp welcome message sent successfully to {mobile_number}")
                    serialized_enquiry['whatsapp_sent'] = True
                    serialized_enquiry['whatsapp_message_id'] = whatsapp_result.get('message_id')
                    serialized_enquiry['whatsapp_message_type'] = message_type
                    serialized_enquiry['whatsapp_error'] = None
                    # Add notification
                    serialized_enquiry['whatsapp_notification'] = whatsapp_result.get('notification', 'WhatsApp message sent successfully')
                else:
                    error_msg = whatsapp_result.get('error', 'Unknown error')
                    solution = whatsapp_result.get('solution', '')
                    status_code = whatsapp_result.get('status_code')
                    
                    logger.warning(f"Failed to send WhatsApp message: {error_msg}")
                    
                    # Provide more specific error messages for common issues
                    user_friendly_error = "WhatsApp message failed to send"
                    
                    if status_code == 466:
                        user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                    elif "quota exceeded" in error_msg.lower():
                        user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                    elif "unauthorized" in error_msg.lower() or status_code == 401:
                        user_friendly_error = "GreenAPI authentication failed - Check API credentials"
                    elif "forbidden" in error_msg.lower() or status_code == 403:
                        user_friendly_error = "GreenAPI access forbidden - Check API permissions"
                    elif "bad request" in error_msg.lower() or status_code == 400:
                        user_friendly_error = "Invalid phone number format or WhatsApp not available for this number"
                    elif "not found" in error_msg.lower() or status_code == 404:
                        user_friendly_error = "GreenAPI endpoint not found - Check API configuration"
                    elif "network error" in error_msg.lower():
                        user_friendly_error = "Network connection error - Check internet connectivity"
                    else:
                        # For other errors, show the original error message
                        user_friendly_error = error_msg
                    
                    serialized_enquiry['whatsapp_sent'] = False
                    serialized_enquiry['whatsapp_error'] = user_friendly_error
                    
                    # Add notification for quota exceeded
                    if status_code == 466 or "quota exceeded" in error_msg.lower():
                        serialized_enquiry['whatsapp_notification'] = "⚠️ GreenAPI monthly quota exceeded. Please upgrade your GreenAPI plan to send messages to more numbers."
                    
                    # Also include the original error for debugging
                    if solution:
                        serialized_enquiry['whatsapp_debug_error'] = f"{error_msg}. Solution: {solution}"
                    else:
                        serialized_enquiry['whatsapp_debug_error'] = error_msg
            else:
                logger.error("WhatsApp service is not initialized")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "WhatsApp service not available - Check GreenAPI configuration"
                
        except Exception as whatsapp_error:
            logger.error(f"WhatsApp service error: {str(whatsapp_error)}")
            serialized_enquiry['whatsapp_sent'] = False
            serialized_enquiry['whatsapp_error'] = str(whatsapp_error)
        
        logger.info(f"Successfully created public enquiry {result.inserted_id}")
        return jsonify(serialized_enquiry), 201
        
    except Exception as e:
        logger.error(f"Error creating public enquiry: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@enquiry_bp.route('/enquiries/<enquiry_id>', methods=['PUT'])
@jwt_required()
def update_enquiry(enquiry_id):
    """Update an existing enquiry"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500

    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        logger.info(f"User {current_user} updating enquiry {enquiry_id}")
        
        # Validate ObjectId
        if not ObjectId.is_valid(enquiry_id):
            return jsonify({'error': 'Invalid enquiry ID'}), 400
        
        # Check if enquiry exists
        existing_enquiry = enquiries_collection.find_one({'_id': ObjectId(enquiry_id)})
        if not existing_enquiry:
            return jsonify({'error': 'Enquiry not found'}), 404
        
        # Check if staff is already assigned and locked
        if existing_enquiry.get('staff_locked', False) and 'staff' in data:
            old_staff = existing_enquiry.get('staff', '')
            new_staff = data['staff']
            # Only allow staff changes if it's the same staff member or if staff is being cleared
            if new_staff and new_staff.strip() != '' and new_staff != old_staff:
                return jsonify({'error': 'Staff assignment is locked. Cannot change assigned staff member.'}), 400
        
        # Validate mobile numbers if provided (accept 10-15 digits with country code)
        if 'mobile_number' in data:
            mobile_number = str(data['mobile_number']).strip()
            if not mobile_number.isdigit() or len(mobile_number) < 10 or len(mobile_number) > 15:
                return jsonify({'error': 'Mobile number must be 10-15 digits (with country code)'}), 400
        
        if 'secondary_mobile_number' in data and data['secondary_mobile_number']:
            secondary_mobile = str(data['secondary_mobile_number']).strip()
            if not secondary_mobile.isdigit() or len(secondary_mobile) < 10 or len(secondary_mobile) > 15:
                return jsonify({'error': 'Secondary mobile number must be 10-15 digits (with country code)'}), 400
        
        # Validate GST status if GST is Yes
        gst_value = str(data.get('gst', existing_enquiry.get('gst', ''))).strip()
        if gst_value == 'Yes' and not str(data.get('gst_status', existing_enquiry.get('gst_status', ''))).strip():
            return jsonify({'error': 'GST status is required when GST is Yes'}), 400
        
        # Validate business_nature if comment is "Not Eligible"
        if 'comments' in data and data['comments'] == 'Not Eligible':
            business_nature = data.get('business_nature', existing_enquiry.get('business_nature', ''))
            if not business_nature or not str(business_nature).strip():
                return jsonify({'error': 'Business Nature is required when "Not Eligible" comment is selected'}), 400
        
        # Parse date if provided
        if 'date' in data:
            data['date'] = parse_date_safely(data['date'])
        
        # Prepare update document
        update_doc = {
            'updated_at': datetime.now(),
            'updated_by': current_user
        }
        
        # Add fields to update
        updatable_fields = [
            'date', 'wati_name', 'user_name', 'mobile_number', 
            'secondary_mobile_number', 'gst', 'gst_status', 
            'business_type', 'business_nature', 'staff', 'comments', 'additional_comments'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'gst':
                    # Handle GST field specially to allow empty values
                    gst_value = str(data[field]).strip()
                    if gst_value in ['Yes', 'No']:
                        update_doc[field] = gst_value
                    else:
                        # Allow empty GST value (will be displayed as "Not Selected" in frontend)
                        update_doc[field] = ''
                elif isinstance(data[field], str):
                    update_doc[field] = data[field].strip() or None
                else:
                    update_doc[field] = data[field]
        
        # Update enquiry
        result = enquiries_collection.update_one(
            {'_id': ObjectId(enquiry_id)},
            {'$set': update_doc}
        )
        
        if result.modified_count == 0:
            return jsonify({'error': 'No changes made'}), 400
        
        # Retrieve updated enquiry
        updated_enquiry = enquiries_collection.find_one({'_id': ObjectId(enquiry_id)})
        serialized_enquiry = serialize_enquiry(updated_enquiry)
        
        # Send WhatsApp message when enquiry is updated (similar to create_enquiry)
        try:
            if whatsapp_service is not None and updated_enquiry is not None:
                # Check if comments have changed
                if 'comments' in data:
                    # Handle None values and ensure proper string comparison
                    old_comments = existing_enquiry.get('comments')
                    new_comments = data['comments']
                    
                    # Convert to strings and strip whitespace for comparison
                    old_comments_str = str(old_comments).strip() if old_comments is not None else ''
                    new_comments_str = str(new_comments).strip() if new_comments is not None else ''
                    
                    # Only send WhatsApp message if comments actually changed
                    if new_comments_str != old_comments_str:
                        logger.info(f"Comments changed from '{old_comments_str}' to '{new_comments_str}', sending WhatsApp message")
                        
                        # Determine message type based on new comments
                        message_type = whatsapp_service.get_comment_message_type(new_comments_str)
                        logger.info(f"Determined message type for updated enquiry: {message_type}")
                        
                        # Send WhatsApp message for updated enquiry
                        whatsapp_result = whatsapp_service.send_enquiry_message(
                            updated_enquiry, 
                            message_type=message_type
                        )
                        
                        if whatsapp_result['success']:
                            logger.info(f"WhatsApp update message sent successfully to {updated_enquiry.get('mobile_number', 'unknown number')}")
                            serialized_enquiry['whatsapp_sent'] = True
                            serialized_enquiry['whatsapp_message_id'] = whatsapp_result.get('message_id')
                            serialized_enquiry['whatsapp_message_type'] = message_type
                            serialized_enquiry['whatsapp_error'] = None
                            # Add notification
                            serialized_enquiry['whatsapp_notification'] = whatsapp_result.get('notification', 'WhatsApp message sent successfully')
                        else:
                            error_msg = whatsapp_result.get('error', 'Unknown error')
                            solution = whatsapp_result.get('solution', '')
                            status_code = whatsapp_result.get('status_code')
                            
                            logger.warning(f"Failed to send WhatsApp update message: {error_msg}")
                            
                            # Provide more specific error messages for common issues
                            user_friendly_error = "WhatsApp message failed to send"
                            
                            if status_code == 466:
                                user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                            elif "quota exceeded" in error_msg.lower():
                                user_friendly_error = "Free plan limit reached - Upgrade GreenAPI plan to send messages to more numbers"
                            elif "unauthorized" in error_msg.lower() or status_code == 401:
                                user_friendly_error = "GreenAPI authentication failed - Check API credentials"
                            elif "forbidden" in error_msg.lower() or status_code == 403:
                                user_friendly_error = "GreenAPI access forbidden - Check API permissions"
                            elif "bad request" in error_msg.lower() or status_code == 400:
                                user_friendly_error = "Invalid phone number format or WhatsApp not available for this number"
                            elif "not found" in error_msg.lower() or status_code == 404:
                                user_friendly_error = "GreenAPI endpoint not found - Check API configuration"
                            elif "network error" in error_msg.lower():
                                user_friendly_error = "Network connection error - Check internet connectivity"
                            else:
                                # For other errors, show the original error message
                                user_friendly_error = error_msg
                            
                            serialized_enquiry['whatsapp_sent'] = False
                            serialized_enquiry['whatsapp_error'] = user_friendly_error
                            
                            # Add notification for quota exceeded
                            if status_code == 466 or "quota exceeded" in error_msg.lower():
                                serialized_enquiry['whatsapp_notification'] = "⚠️ GreenAPI monthly quota exceeded. Please upgrade your GreenAPI plan to send messages to more numbers."
                            
                            # Also include the original error for debugging
                            if solution:
                                serialized_enquiry['whatsapp_debug_error'] = f"{error_msg}. Solution: {solution}"
                            else:
                                serialized_enquiry['whatsapp_debug_error'] = error_msg
                
                # Check if staff has been assigned
                if 'staff' in data:
                    new_staff = data['staff']
                    
                    # Always send staff assignment messages when staff is assigned/changed
                    # Remove the condition that only sent messages on first assignment
                    if new_staff and new_staff.strip() != '' and new_staff != 'None':
                        logger.info(f"Staff assigned/updated to '{new_staff}', sending staff assignment messages")
                        
                        # Send the three staff assignment messages
                        whatsapp_result = whatsapp_service.send_staff_assignment_messages(
                            updated_enquiry, 
                            new_staff
                        )
                        
                        if whatsapp_result['success']:
                            logger.info(f"Staff assignment messages sent successfully to {updated_enquiry.get('mobile_number', 'unknown number')}")
                            serialized_enquiry['whatsapp_sent'] = True
                            serialized_enquiry['whatsapp_message_id'] = 'staff_assignment_' + str(int(datetime.utcnow().timestamp()))
                            serialized_enquiry['whatsapp_message_type'] = 'staff_assignment'
                            serialized_enquiry['whatsapp_error'] = None
                            # Add notification
                            serialized_enquiry['whatsapp_notification'] = whatsapp_result.get('notification', 'WhatsApp staff assignment messages sent successfully')
                            
                            # Remove staff locking - allow staff to be reassigned to other enquiries
                            # Do not lock the staff assignment
                            logger.info(f"Staff assignment completed for enquiry {enquiry_id} - staff not locked")
                        else:
                            error_msg = whatsapp_result.get('error', 'Unknown error')
                            logger.warning(f"Failed to send staff assignment messages: {error_msg}")
                            
                            serialized_enquiry['whatsapp_sent'] = False
                            serialized_enquiry['whatsapp_error'] = f"Staff assignment messages failed: {error_msg}"
                            
                            # Add notification for quota exceeded
                            if "quota exceeded" in error_msg.lower() or "466" in str(whatsapp_result.get('status_code', '')):
                                serialized_enquiry['whatsapp_notification'] = "⚠️ GreenAPI monthly quota exceeded. Please upgrade your GreenAPI plan to send messages to more numbers."
                            else:
                                serialized_enquiry['whatsapp_notification'] = f"⚠️ WhatsApp staff assignment messages failed: {error_msg}"
            elif whatsapp_service is None:
                logger.error("WhatsApp service is not initialized")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "WhatsApp service not available - Check GreenAPI configuration"
            elif updated_enquiry is None:
                logger.error("Failed to retrieve updated enquiry")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "Failed to retrieve updated enquiry"
                
        except Exception as whatsapp_error:
            logger.error(f"WhatsApp service error during update: {str(whatsapp_error)}")
            serialized_enquiry['whatsapp_sent'] = False
            serialized_enquiry['whatsapp_error'] = str(whatsapp_error)
        
        logger.info(f"Updated enquiry {enquiry_id} by user {current_user}")
        return jsonify(serialized_enquiry), 200
        
    except Exception as e:
        logger.error(f"Error updating enquiry {enquiry_id}: {e}")
        return jsonify({'error': 'Failed to update enquiry'}), 500

@enquiry_bp.route('/enquiries/<enquiry_id>', methods=['DELETE'])
@jwt_required()
def delete_enquiry(enquiry_id):
    """Delete an enquiry"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} deleting enquiry {enquiry_id}")
        
        # Validate ObjectId
        if not ObjectId.is_valid(enquiry_id):
            return jsonify({'error': 'Invalid enquiry ID'}), 400
        
        # Check if enquiry exists
        existing_enquiry = enquiries_collection.find_one({'_id': ObjectId(enquiry_id)})
        if not existing_enquiry:
            return jsonify({'error': 'Enquiry not found'}), 404
        
        # Delete enquiry
        result = enquiries_collection.delete_one({'_id': ObjectId(enquiry_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Failed to delete enquiry'}), 500
        
        logger.info(f"Deleted enquiry {enquiry_id} by user {current_user}")
        return jsonify({'message': 'Enquiry deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting enquiry {enquiry_id}: {e}")
        return jsonify({'error': 'Failed to delete enquiry'}), 500

@enquiry_bp.route('/enquiries/stats', methods=['GET'])
@jwt_required()
def get_enquiry_stats():
    """Get enquiry statistics"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        current_user = get_jwt_identity()
        logger.info(f"User {current_user} requesting enquiry stats")
        
        # Get total count
        total_enquiries = enquiries_collection.count_documents({})
        
        # Get count by GST status
        gst_yes_count = enquiries_collection.count_documents({'gst': 'Yes'})
        gst_no_count = enquiries_collection.count_documents({'gst': 'No'})
        
        # Get count by comments (top 5)
        comment_pipeline = [
            {'$group': {'_id': '$comments', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        comment_stats = list(enquiries_collection.aggregate(comment_pipeline))
        
        # Get count by staff (top 5)
        staff_pipeline = [
            {'$group': {'_id': '$staff', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': 5}
        ]
        staff_stats = list(enquiries_collection.aggregate(staff_pipeline))
        
        stats = {
            'total_enquiries': total_enquiries,
            'gst_yes': gst_yes_count,
            'gst_no': gst_no_count,
            'top_comments': comment_stats,
            'top_staff': staff_stats
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting enquiry stats: {e}")
        return jsonify({'error': 'Failed to get enquiry statistics'}), 500

@enquiry_bp.route('/whatsapp/test', methods=['POST'])
@jwt_required()
def test_whatsapp():
    """Test WhatsApp message sending"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'mobile_number' not in data:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        mobile_number = data['mobile_number']
        message_type = data.get('message_type', 'new_enquiry')
        
        # Log the incoming data for debugging
        logger.info(f"📱 WhatsApp test request - User: {current_user}, Mobile: {mobile_number}, Type: {message_type}")
        
        # Create test enquiry data
        test_enquiry = {
            'wati_name': data.get('wati_name', 'Test Customer'),
            'mobile_number': mobile_number,
            'comments': data.get('comments', 'Test message')
        }
        
        logger.info(f"User {current_user} testing WhatsApp message to {mobile_number}")
        logger.info(f"Test data: {test_enquiry}")
        
        # Log WhatsApp service status for debugging
        logger.info(f"WhatsApp service status: {whatsapp_service is not None}")
        if whatsapp_service is not None:
            logger.info(f"WhatsApp service API available: {getattr(whatsapp_service, 'api_available', 'Unknown')}")
            logger.info(f"WhatsApp service instance ID: {getattr(whatsapp_service, 'instance_id', 'Unknown')}")
        
        # Check if WhatsApp service is available
        if whatsapp_service is None:
            # Try to re-import the service as a fallback
            try:
                from greenapi_whatsapp_service import whatsapp_service as fresh_whatsapp_service
                if fresh_whatsapp_service is not None and getattr(fresh_whatsapp_service, 'api_available', False):
                    logger.info("🔄 Fresh WhatsApp service import successful")
                    # Send test message with fresh service
                    result = fresh_whatsapp_service.send_enquiry_message(test_enquiry, message_type)
                else:
                    logger.error("❌ Fresh WhatsApp service import failed or not available")
                    return jsonify({
                        'success': False,
                        'error': 'GreenAPI WhatsApp service is not initialized. Check GREENAPI_INSTANCE_ID and GREENAPI_TOKEN in .env file.',
                        'mobile_number': mobile_number,
                        'message_type': message_type,
                        'solution': 'Verify GreenAPI credentials in .env file'
                    }), 500
            except Exception as import_error:
                logger.error(f"❌ WhatsApp service re-import failed: {import_error}")
                return jsonify({
                    'success': False,
                    'error': 'GreenAPI WhatsApp service is not initialized. Check GREENAPI_INSTANCE_ID and GREENAPI_TOKEN in .env file.',
                    'mobile_number': mobile_number,
                    'message_type': message_type,
                    'solution': 'Verify GreenAPI credentials in .env file'
                }), 500
        else:
            # Check if service is properly configured
            if not hasattr(whatsapp_service, 'api_available') or not whatsapp_service.api_available:
                return jsonify({
                    'success': False,
                    'error': 'GreenAPI service is not properly configured.',
                    'mobile_number': mobile_number,
                    'message_type': message_type,
                    'solution': 'Check GREENAPI_INSTANCE_ID and GREENAPI_TOKEN values'
                }), 500
            
            # Send test message
            result = whatsapp_service.send_enquiry_message(test_enquiry, message_type)
        
        logger.info(f"WhatsApp test result: {result}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'WhatsApp test message sent successfully',
                'message_id': result.get('message_id'),
                'mobile_number': mobile_number,
                'message_type': message_type
            }), 200
        else:
            error_msg = result.get('error', 'Unknown error')
            solution = result.get('solution', '')
            status_code = result.get('status_code', 400)  # Default to 400 for client errors
            
            response_data = {
                'success': False,
                'error': error_msg,
                'mobile_number': mobile_number,
                'message_type': message_type
            }
            
            # Include additional debugging information
            if 'formatted_phone_number' in result:
                response_data['formatted_phone_number'] = result['formatted_phone_number']
            if 'status_code' in result:
                response_data['status_code'] = result['status_code']
            if 'response' in result:
                response_data['api_response'] = result['response']
            
            # Special handling for quota exceeded errors (466 or specific error messages)
            if 'quota exceeded' in error_msg.lower() or 'monthly quota' in error_msg.lower() or status_code == 466:
                # For testing purposes, allow testing to any number by returning success
                # This allows admins to test WhatsApp functionality even when quota is exceeded
                logger.info(f"Quota exceeded for user {current_user}, but allowing test for {mobile_number}")
                return jsonify({
                    'success': True,
                    'message': f'WhatsApp test message simulated successfully (Quota exceeded - Mock response)',
                    'message_id': f'mock_test_{mobile_number}',
                    'mobile_number': mobile_number,
                    'message_type': message_type,
                    'mock_response': True,
                    'quota_exceeded': True,
                    'note': 'This is a simulated response since GreenAPI quota is exceeded. Upgrade plan for real messaging.'
                }), 200
            
            # Special handling for phone number format errors
            elif 'bad request' in error_msg.lower() or status_code == 400:
                response_data['solution'] = 'Ensure the phone number is in international format (e.g., +919876543210) and the recipient has WhatsApp. Numbers should contain only digits and optional country code prefix.'
            
            if solution:
                response_data['solution'] = solution
                response_data['detailed_error'] = f"{error_msg}. Solution: {solution}"
            
            # Return appropriate status code based on error type
            # Use 466 for quota exceeded to distinguish from other errors
            final_status_code = 466 if response_data.get('quota_exceeded') else (status_code if status_code in [400, 401, 403, 404, 466] else 400)
            return jsonify(response_data), final_status_code
            
    except Exception as e:
        logger.error(f"Error testing WhatsApp: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'WhatsApp test failed: {str(e)}'}), 500

@enquiry_bp.route('/whatsapp/test-unlimited', methods=['POST'])
@jwt_required()
def test_whatsapp_unlimited():
    """Test WhatsApp message sending - Always allows testing regardless of quota"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if not data or 'mobile_number' not in data:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        mobile_number = data['mobile_number']
        message_type = data.get('message_type', 'new_enquiry')
        wati_name = data.get('wati_name', 'Test Customer')
        
        logger.info(f"📱 WhatsApp unlimited test request - User: {current_user}, Mobile: {mobile_number}")
        
        # Always return success for testing purposes
        # This allows testing UI functionality without quota restrictions
        return jsonify({
            'success': True,
            'message': f'WhatsApp test message simulated successfully for {wati_name}',
            'message_id': f'test_unlimited_{mobile_number}_{int(time.time())}',
            'mobile_number': mobile_number,
            'message_type': message_type,
            'wati_name': wati_name,
            'test_mode': True,
            'note': 'This is a test simulation that bypasses quota restrictions. Use regular /whatsapp/test for real messaging.'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in unlimited WhatsApp test: {str(e)}")
        return jsonify({'error': f'Test failed: {str(e)}'}), 500

@enquiry_bp.route('/whatsapp/greenapi-test', methods=['POST'])
@jwt_required()
def test_whatsapp_greenapi():
    """Test WhatsApp message sending via GreenAPI (no OTP required)"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        logger.info(f"📱 GreenAPI test request data: {data}")
        
        if not data or 'mobile_number' not in data:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        mobile_number = data['mobile_number']
        message = data.get('message', f'🚀 GreenAPI test message from TMIS to {mobile_number}')
        
        logger.info(f"User {current_user} testing GreenAPI WhatsApp to {mobile_number}")
        logger.info(f"Message content: {message}")
        
        # Log WhatsApp service status for debugging
        logger.info(f"WhatsApp service status: {whatsapp_service is not None}")
        if whatsapp_service is not None:
            logger.info(f"WhatsApp service API available: {getattr(whatsapp_service, 'api_available', 'Unknown')}")
            logger.info(f"WhatsApp service instance ID: {getattr(whatsapp_service, 'instance_id', 'Unknown')}")
        
        # Check if WhatsApp service is available
        if whatsapp_service is None:
            # Try to re-import the service as a fallback
            try:
                from greenapi_whatsapp_service import whatsapp_service as fresh_whatsapp_service
                if fresh_whatsapp_service is not None:
                    logger.info("🔄 Fresh WhatsApp service import successful")
                    # Send message using fresh service
                    result = fresh_whatsapp_service.send_message(mobile_number, message)
                else:
                    logger.error("❌ Fresh WhatsApp service import failed")
                    return jsonify({
                        'success': False,
                        'error': 'GreenAPI WhatsApp service is not initialized. Check environment variables.',
                        'mobile_number': mobile_number
                    }), 500
            except Exception as import_error:
                logger.error(f"❌ WhatsApp service re-import failed: {import_error}")
                return jsonify({
                    'success': False,
                    'error': 'GreenAPI WhatsApp service is not initialized. Check environment variables.',
                    'mobile_number': mobile_number
                }), 500
        else:
            # Send message using GreenAPI
            result = whatsapp_service.send_message(mobile_number, message)
        
        logger.info(f"GreenAPI test result: {result}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'GreenAPI WhatsApp message sent successfully (no OTP required)',
                'message_id': result.get('message_id'),
                'mobile_number': mobile_number,
                'service': 'GreenAPI',
                'no_otp_required': True
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error'),
                'solution': result.get('solution'),
                'mobile_number': mobile_number,
                'service': 'GreenAPI',
                'debug_info': {
                    'original_phone_number': result.get('original_phone_number'),
                    'formatted_phone_number': result.get('formatted_phone_number'),
                    'status_code': result.get('status_code'),
                    'response': result.get('response')
                }
            }), 400
            
    except Exception as e:
        logger.error(f"Error testing GreenAPI WhatsApp: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'GreenAPI WhatsApp test failed: {str(e)}'}), 500

@enquiry_bp.route('/whatsapp/debug', methods=['GET'])
@jwt_required()
def debug_whatsapp_service():
    """Debug WhatsApp service status"""
    try:
        debug_info = {
            'service_initialized': whatsapp_service is not None,
            'service_type': 'GreenAPI',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if whatsapp_service is not None:
            debug_info.update({
                'api_available': getattr(whatsapp_service, 'api_available', False),
                'instance_id': getattr(whatsapp_service, 'instance_id', None),
                'base_url': getattr(whatsapp_service, 'base_url', None),
                'has_token': bool(getattr(whatsapp_service, 'token', None))
            })
            
            # Try to check status
            try:
                status = whatsapp_service.check_status()
                debug_info['connection_status'] = status
            except Exception as status_error:
                debug_info['connection_status'] = {'error': str(status_error)}
        else:
            debug_info['error'] = 'WhatsApp service is None'
            
        return jsonify(debug_info), 200
        
    except Exception as e:
        logger.error(f"Error debugging WhatsApp service: {str(e)}")
        return jsonify({'error': f'Debug failed: {str(e)}'}), 500

@enquiry_bp.route('/whatsapp/templates', methods=['GET'])
@jwt_required()
def get_whatsapp_templates():
    """Get available WhatsApp message templates"""
    try:
        if whatsapp_service is None:
            return jsonify({
                'error': 'WhatsApp service not initialized',
                'solution': 'Check GreenAPI credentials'
            }), 500
            
        templates = whatsapp_service.get_message_templates()
        
        # Return template names and preview of messages
        template_info = {}
        for template_name, template_content in templates.items():
            # Show first 100 characters as preview
            preview = template_content.replace('{wati_name}', '[Customer Name]')
            preview = preview.replace('{comments}', '[Status]')
            template_info[template_name] = {
                'name': template_name,
                'preview': preview[:100] + '...' if len(preview) > 100 else preview,
                'full_template': template_content
            }
        
        return jsonify({
            'templates': template_info,
            'available_types': list(templates.keys())
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp templates: {str(e)}")
        return jsonify({'error': f'Failed to get templates: {str(e)}'}), 500

# Add a simple test endpoint to verify the new code is running
# Force redeployment comment added 2025-10-09
@enquiry_bp.route('/enquiries/whatsapp/webhook/test', methods=['GET'])
def test_webhook_handler():
    """Test endpoint to verify the new webhook handler is running"""
    return jsonify({
        'status': 'success',
        'message': 'Enhanced webhook handler is running with username capture fix',
        'version': '2.1',
        'timestamp': datetime.utcnow().isoformat(),
        'features': [
            'WhatsApp username capture',
            'Enhanced mobile number extraction', 
            'Duplicate prevention',
            'Comprehensive logging',
            'Multiple sender name field support'
        ]
    }), 200

@enquiry_bp.route('/enquiries/whatsapp/webhook/test-data', methods=['POST'])
def test_webhook_with_data():
    """Test endpoint to simulate webhook data processing"""
    try:
        # Get test data or use default
        data = request.get_json() or {
            "typeWebhook": "incomingMessageReceived",
            "messageData": {
                "textMessage": {
                    "text": "Hi I am interested!"
                },
                "idMessage": "test_message_" + str(int(datetime.utcnow().timestamp()))
            },
            "senderData": {
                "chatId": "918106811285@c.us",
                "senderName": "Test User",
                "pushName": "Test WhatsApp User",
                "chatName": "Test Chat Name"
            }
        }
        
        logger.info(f"🧪 Testing webhook with data: {data}")
        
        # Extract message info using our enhanced function
        message_info = _extract_message_info(data)
        
        # Test the enquiry creation logic without actually creating
        chat_id = message_info.get('chat_id', '')
        sender_name = message_info.get('sender_name', '')
        message_text = message_info.get('message_text', '')
        
        # Clean mobile number
        sender_number = chat_id.replace('@c.us', '')
        clean_number = ''.join(filter(str.isdigit, sender_number))
        
        # Determine display name
        if sender_name and sender_name.strip():
            display_name = sender_name.strip()
        else:
            display_name = f"WhatsApp User ({clean_number})"
        
        return jsonify({
            'status': 'success',
            'message': 'Webhook data processing test completed',
            'extracted_info': message_info,
            'processed_data': {
                'display_name': display_name,
                'whatsapp_username': sender_name,
                'mobile_number': clean_number,
                'original_chat_id': chat_id,
                'message_text': message_text
            },
            'would_create_enquiry': message_info.get('has_message_data', False) and _is_interested_message(message_text),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Test webhook error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Test failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@enquiry_bp.route('/enquiries/whatsapp/webhook', methods=['GET', 'POST'])
def handle_incoming_whatsapp():
    """Handle incoming WhatsApp messages from GreenAPI webhook"""
    
    # Handle GET requests for testing
    if request.method == 'GET':
        logger.info(f"🔍 GET request to webhook endpoint from {request.remote_addr}")
        return jsonify({
            'status': 'webhook_endpoint_active',
            'message': 'Webhook endpoint is ready to receive POST requests from GreenAPI',
            'timestamp': datetime.utcnow().isoformat(),
            'method_received': 'GET',
            'expected_method': 'POST'
        }), 200
    
    try:
        # Get the incoming data
        data = request.get_json()
        
        # Log ALL incoming requests for debugging
        logger.info(f"📥 === NEW WEBHOOK REQUEST === {datetime.utcnow().isoformat()}")
        logger.info(f"📥 Request Headers: {dict(request.headers)}")
        logger.info(f"📥 Request Method: {request.method}")
        logger.info(f"📥 Request URL: {request.url}")
        logger.info(f"📥 Raw Data: {request.get_data(as_text=True)}")
        logger.info(f"📥 Parsed JSON Data: {data}")
        logger.info(f"📥 Data type: {type(data)}")
        logger.info(f"📥 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Always return success for debugging - even for non-message events
        # This helps us see what GreenAPI is actually sending
        if not data:
            logger.warning("⚠️ Empty webhook data received - but responding with success")
        
        # Handle empty data
        if not data:
            logger.warning("⚠️ Empty webhook data received")
            return jsonify({
                'success': True,
                'message': 'Empty data received'
            }), 200
        
        # Check if this is a state change notification or other non-message event (ignore these)
        webhook_type = data.get('typeWebhook', '')
        logger.info(f"🔍 Webhook type: '{webhook_type}'")
        
        if webhook_type and webhook_type not in ['incomingMessageReceived', 'outgoingMessageReceived']:
            logger.info(f"ℹ️ Non-message webhook event received: {webhook_type}")
            return jsonify({
                'success': True,
                'message': f'Webhook event {webhook_type} received and ignored'
            }), 200
        
        # Extract message information from various possible formats
        message_info = _extract_message_info(data)
        logger.info(f"📦 Extracted message info: {message_info}")
        
        # If we couldn't extract message info, it might be a non-message event
        if not message_info.get('has_message_data'):
            logger.info("ℹ️ No message data found in webhook, ignoring")
            
            # Emit notification for non-message webhook
            try:
                from app import socketio
                notification = {
                    'type': 'webhook_status',
                    'status': 'info',
                    'message': "🔔 WEBHOOK RECEIVED: Non-message event (state change, status update, etc.)",
                    'details': {
                        'webhook_type': data.get('typeWebhook', 'unknown'),
                        'enquiry_created': False,
                        'reason': 'Not a message event'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                socketio.emit('webhook_notification', notification)
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': 'No message data found'
            }), 200
        
        chat_id = message_info.get('chat_id', '')
        message_text = message_info.get('message_text', '')
        sender_name = message_info.get('sender_name', '')
        message_id = message_info.get('message_id', '')
        
        # Log the extracted information
        logger.info(f"📋 Extracted Information:")
        logger.info(f"   Chat ID: {chat_id}")
        logger.info(f"   Message Text: {message_text}")
        logger.info(f"   Sender Name: {sender_name}")
        logger.info(f"   Message ID: {message_id}")
        
        # Check if we have the minimum required data
        if not message_text:
            logger.info("ℹ️ No message text found, ignoring")
            return jsonify({
                'success': True,
                'message': 'No message text found'
            }), 200
        
        # Log the exact message text for debugging
        logger.info(f"🔍 Raw message text: '{message_text}'")
        logger.info(f"🔍 Message text length: {len(message_text)}")
        logger.info(f"🔍 Message text repr: {repr(message_text)}")
        
        # Check if this is one of our reply options
        is_reply_option = _is_reply_option(message_text)
        logger.info(f"🔍 Is reply option: {is_reply_option}")
        
        # Check if this is one of our reply options
        if _is_reply_option(message_text):
            logger.info(f"🔄 Processing reply option from {data.get('senderName', '') or chat_id}: {message_text}")
            # Send appropriate response
            response_text = _get_reply_response(message_text)
            if whatsapp_service and whatsapp_service.api_available:
                # Use the proper method to send the message
                logger.info(f"📤 Sending reply message: {response_text}")
                result = whatsapp_service.send_message(chat_id, response_text)
                if result['success']:
                    logger.info(f"✅ Reply sent for option '{message_text}' to {chat_id}")
                else:
                    logger.error(f"❌ Failed to send reply for option '{message_text}' to {chat_id}: {result.get('error')}")
                    # Log additional error details
                    logger.error(f"❌ Error details: {result}")
                    
                    # Check for quota exceeded error
                    error_msg = result.get('error', '').lower()
                    status_code = result.get('status_code', 0)
                    
                    if 'quota exceeded' in error_msg or 'monthly quota' in error_msg or status_code == 466:
                        logger.warning(f"⚠️ GreenAPI quota exceeded when sending reply to {chat_id}")
                        # Still return success to the webhook (we don't want to cause webhook errors)
                        # but log the quota issue
            else:
                logger.error("❌ WhatsApp service not available")
            return jsonify({
                'success': True,
                'message': 'Reply option processed'
            }), 200
        # Check if this is the "I am interested" message
        else:
            is_interested = _is_interested_message(message_text)
            logger.info(f"🔍 Is interested message: {is_interested}")
            
            if is_interested:
                logger.info(f"✅ Processing interested message from {sender_name or chat_id}: {message_text}")
                return _create_enquiry_from_message(chat_id, message_text, sender_name, message_id)
            else:
                logger.info(f"📥 Received WhatsApp message but not 'interested' message: {message_text}")
                return jsonify({
                    'success': True,
                    'message': 'Message received but not processed as enquiry'
                }), 200
        
    except Exception as e:
        logger.error(f"❌ Error handling incoming WhatsApp message: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Error processing webhook: {str(e)}'
        }), 500

def _extract_message_info(data):
    """Extract message information from various GreenAPI webhook formats"""
    result = {
        'has_message_data': False,
        'chat_id': '',
        'message_text': '',
        'sender_name': '',
        'message_id': ''
    }
    
    try:
        # Log the data structure for debugging
        logger.info(f"🔍 Extracting message info from data structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Handle different GreenAPI webhook formats
        
        # Format 1: Direct message format (original) - This works
        if 'message' in data and 'chatId' in data and not data.get('typeWebhook'):
            logger.info("📦 Processing Format 1: Direct message format")
            message_data = data['message']
            result['chat_id'] = data['chatId']
            result['sender_name'] = data.get('senderName', '')
            result['message_text'] = message_data.get('textMessage', {}).get('text', '')
            result['message_id'] = message_data.get('idMessage', '')
            result['has_message_data'] = True
            
        # Format 2: Incoming message received format with messageData
        elif data.get('typeWebhook') == 'incomingMessageReceived' and 'messageData' in data:
            logger.info("📦 Processing Format 2: Incoming message with messageData")
            message_data = data.get('messageData', {})
            sender_data = data.get('senderData', {})
            
            # Extract text message - handle different possible structures
            if isinstance(message_data, dict):
                # Check for textMessage structure
                if 'textMessage' in message_data and isinstance(message_data['textMessage'], dict):
                    result['message_text'] = message_data['textMessage'].get('text', '')
                # Check for direct text in messageData
                elif 'text' in message_data:
                    result['message_text'] = message_data.get('text', '')
                
                # Extract message ID
                result['message_id'] = message_data.get('idMessage', '')
                
            # Extract chat ID and sender name from senderData
            if isinstance(sender_data, dict):
                result['chat_id'] = sender_data.get('chatId', '')
                
                # Try multiple fields for sender name with priority order
                sender_name_options = [
                    sender_data.get('senderName', ''),
                    sender_data.get('chatName', ''),
                    sender_data.get('pushName', ''),  # WhatsApp push name
                    sender_data.get('notifyName', '')  # WhatsApp notify name
                ]
                
                # Use the first non-empty name
                for name_option in sender_name_options:
                    if name_option and name_option.strip():
                        result['sender_name'] = name_option.strip()
                        break
                
                logger.info(f"📋 Sender data fields: {list(sender_data.keys())}")
                logger.info(f"📋 Selected sender name: '{result['sender_name']}'")
                
            result['has_message_data'] = bool(result['message_text'])  # Only mark as having data if there's text
                
        # Format 3: Incoming message received format with direct message
        elif data.get('typeWebhook') == 'incomingMessageReceived' and 'message' in data:
            logger.info("📦 Processing Format 3: Incoming message with direct message")
            msg = data['message']
            sender_data = data.get('senderData', {})
            
            if isinstance(msg, dict):
                result['message_text'] = msg.get('textMessage', {}).get('text', '')
                result['message_id'] = msg.get('idMessage') or msg.get('id', '')
                
            # Get sender info from senderData with enhanced name extraction
            if isinstance(sender_data, dict):
                result['chat_id'] = sender_data.get('chatId', '')
                
                # Try multiple fields for sender name with priority order
                sender_name_options = [
                    sender_data.get('senderName', ''),
                    sender_data.get('chatName', ''),
                    sender_data.get('pushName', ''),  # WhatsApp push name
                    sender_data.get('notifyName', '')  # WhatsApp notify name
                ]
                
                # Use the first non-empty name
                for name_option in sender_name_options:
                    if name_option and name_option.strip():
                        result['sender_name'] = name_option.strip()
                        break
                        
                logger.info(f"📋 Sender data fields: {list(sender_data.keys())}")
                logger.info(f"📋 Selected sender name: '{result['sender_name']}'")
                
            result['has_message_data'] = bool(result['message_text'])
            
        # Format 4: Alternative format with text directly in data
        elif data.get('typeWebhook') == 'incomingMessageReceived' and 'text' in data:
            logger.info("📦 Processing Format 4: Direct text format")
            result['message_text'] = data.get('text', '')
            result['message_id'] = data.get('idMessage', '')
            
            sender_data = data.get('senderData', {})
            if isinstance(sender_data, dict):
                result['chat_id'] = sender_data.get('chatId', '')
                
                # Try multiple fields for sender name with priority order
                sender_name_options = [
                    sender_data.get('senderName', ''),
                    sender_data.get('chatName', ''),
                    sender_data.get('pushName', ''),  # WhatsApp push name
                    sender_data.get('notifyName', '')  # WhatsApp notify name
                ]
                
                # Use the first non-empty name
                for name_option in sender_name_options:
                    if name_option and name_option.strip():
                        result['sender_name'] = name_option.strip()
                        break
                        
                logger.info(f"📋 Sender data fields: {list(sender_data.keys())}")
                logger.info(f"📋 Selected sender name: '{result['sender_name']}'")
                
            result['has_message_data'] = bool(result['message_text'])
            
        # Format 5: Outgoing message format (when you send to yourself)
        elif data.get('typeWebhook') == 'outgoingMessageReceived' and 'messageData' in data:
            logger.info("📦 Processing Format 5: Outgoing message format (self-message)")
            message_data = data.get('messageData', {})
            sender_data = data.get('senderData', {})
            
            # Extract text from textMessageData structure
            if isinstance(message_data, dict):
                text_data = message_data.get('textMessageData', {})
                if isinstance(text_data, dict):
                    result['message_text'] = text_data.get('textMessage', '')
                
                # Get message ID from root level
                result['message_id'] = data.get('idMessage', '')
                
            # Extract sender info
            if isinstance(sender_data, dict):
                result['chat_id'] = sender_data.get('chatId', '')
                
                # Try multiple fields for sender name
                sender_name_options = [
                    sender_data.get('senderName', ''),
                    sender_data.get('chatName', ''),
                    sender_data.get('senderContactName', ''),
                    sender_data.get('sender', '').replace('@c.us', '')
                ]
                
                # Use the first non-empty name
                for name_option in sender_name_options:
                    if name_option and name_option.strip():
                        result['sender_name'] = name_option.strip()
                        break
                        
                logger.info(f"📋 Outgoing message sender data: {list(sender_data.keys())}")
                logger.info(f"📋 Selected sender name: '{result['sender_name']}'")
                
            result['has_message_data'] = bool(result['message_text'])
            
        # Format 6: State change or other notifications (no message data)
        elif data.get('typeWebhook') and 'message' not in data and 'messageData' not in data:
            logger.info("📦 Processing Format 6: Non-message event")
            # This is likely a state change or other notification, not a message
            result['has_message_data'] = False
            
        # Log what we extracted
        logger.info(f"📤 Extracted data: {result}")
            
    except Exception as e:
        logger.error(f"Error extracting message info: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return result

def _is_interested_message(message_text):
    """Check if the message indicates interest"""
    if not message_text:
        return False
    text_lower = message_text.lower()
    return "i am interested" in text_lower or "interested" in text_lower or "i'm interested" in text_lower

def _is_reply_option(message_text):
    """Check if the message is one of the reply options"""
    if not message_text:
        return False
    # Normalize the text for comparison
    text_normalized = message_text.lower().strip()
    logger.info(f"🔍 Checking if '{message_text}' is a reply option (normalized: '{text_normalized}')")
    
    reply_options = ['get loan', 'check eligibility', 'more details']
    is_reply = text_normalized in reply_options
    
    logger.info(f"🔍 Is reply option: {is_reply}")
    if is_reply:
        logger.info(f"🔍 Matched reply option: {text_normalized}")
    
    return is_reply

def _get_reply_response(message_text):
    """Get the appropriate response for reply options"""
    text_lower = message_text.lower().strip()
    
    responses = {
        'get loan': """Business Guru is banking associate for loans especially business loans.

We provide collateral free loans based on turnover for all kinds of business without considering CIBIL scores of the customer/business""",
        
        'check eligibility': """📋 Documents Needed for Eligibility Check 
Please share:  
1️⃣ Business Registration  
2️⃣ GST Certificate  
3️⃣ Company Bank Details  
4️⃣ 6-12 Month Bank Statements  
5️⃣ Website URL  
6️⃣ Owner PAN + Aadhaar  
7️⃣ Business PAN  
8️⃣ Email & Mobile  
- IE Code (Imports/Exports)  
- Intl. Payment Gateway 
- Send photos/PDFs one-by-one  
We'll verify within 4 hours!""",
        
        'more details': """Welcome to Business Guru! We're delighted to have you with us. At Business Guru, we specialize in providing collateral loans to help businesses like yours grow and thrive. Our team of financial experts is ready to assist you with personalized loan solutions tailored to your business needs. We'll be contacting you shortly to discuss your requirements in detail and guide you through our simple application process. 


"""
    }
    
    return responses.get(text_lower, "I didn't understand that. Please reply with one of these options: Get Loan, Check Eligibility, or More Details")

def _process_incoming_message(data):
    """Process incoming message data"""
    try:
        message_data = data['message']
        chat_id = data['chatId']
        
        # Extract sender information
        sender_number = chat_id.replace('@c.us', '')  # Remove @c.us suffix
        message_text = message_data.get('textMessage', {}).get('text', '')
        
        # Check if this is one of our reply options
        if _is_reply_option(message_text):
            logger.info(f"🔄 Processing reply option from {data.get('senderName', '') or chat_id}: {message_text}")
            # Send appropriate response
            response_text = _get_reply_response(message_text)
            if whatsapp_service and whatsapp_service.api_available:
                # Format the phone number properly for GreenAPI
                formatted_number = chat_id  # chat_id already includes @c.us suffix
                result = whatsapp_service.send_message(formatted_number, response_text)
                if result['success']:
                    logger.info(f"✅ Reply sent for option '{message_text}' to {chat_id}")
                else:
                    logger.error(f"❌ Failed to send reply for option '{message_text}' to {chat_id}: {result.get('error')}")
            return jsonify({
                'success': True,
                'message': 'Reply option processed'
            }), 200
        # Check if this is the "I am interested" message
        elif _is_interested_message(message_text):
            return _create_enquiry_from_message(chat_id, message_text, data.get('senderName', ''), message_data.get('idMessage', ''))
        else:
            logger.info(f"📥 Received WhatsApp message but not 'interested' message: {message_text}")
            return jsonify({
                'success': True,
                'message': 'Message received but not processed as enquiry'
            }), 200
            
    except Exception as e:
        logger.error(f"❌ Error processing message data: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing message: {str(e)}'
        }), 500

def _create_enquiry_from_message(chat_id, message_text, sender_name, message_id):
    """Create enquiry record from message data"""
    try:
        # Extract sender information
        sender_number = chat_id.replace('@c.us', '')  # Remove @c.us suffix
        
        # Clean and format mobile number
        # Remove any non-digit characters and ensure proper format
        clean_number = ''.join(filter(str.isdigit, sender_number))
        
        # Log the extracted information for debugging
        logger.info(f"📋 Creating enquiry from WhatsApp message:")
        logger.info(f"   Original Chat ID: {chat_id}")
        logger.info(f"   Extracted Number: {sender_number}")
        logger.info(f"   Clean Number: {clean_number}")
        logger.info(f"   Sender Name: {sender_name}")
        logger.info(f"   Message: {message_text}")
        
        # Determine the display name for the enquiry
        # Handle GreenAPI free version limitations
        if sender_name and sender_name.strip() and sender_name.strip() != 'null' and sender_name.strip() != '':
            display_name = sender_name.strip()
            logger.info(f"   Using sender name: {display_name}")
        else:
            # For free plans, use phone number as identifier
            display_name = f"WhatsApp User {clean_number}"
            logger.info(f"   Using phone-based name (free plan): {display_name}")
            logger.info(f"   Note: Sender name not available in free GreenAPI plan")
        
        # Create a new enquiry record with proper WhatsApp fields
        new_enquiry = {
            'date': datetime.utcnow(),
            'wati_name': display_name,
            'user_name': sender_name if sender_name and sender_name.strip() and sender_name.strip() != 'null' else '',  # Store actual WhatsApp username (may be empty in free plan)
            'mobile_number': clean_number,
            'secondary_mobile_number': None,
            'gst': '',
            'gst_status': '',
            'business_type': '',
            'business_nature': '',
            'staff': 'WhatsApp Bot',  # Default staff assignment
            'comments': 'New Enquiry - Interested',
            'additional_comments': f'Received via WhatsApp: "{message_text}"',
            # WhatsApp specific fields
            'whatsapp_status': 'received',
            'whatsapp_message_id': message_id,
            'whatsapp_chat_id': chat_id,
            'whatsapp_sender_name': sender_name if sender_name and sender_name.strip() and sender_name.strip() != 'null' else 'Not available (Free plan)',
            'whatsapp_message_text': message_text,
            'whatsapp_sent': False,  # No message sent yet, just received
            'source': 'whatsapp_webhook',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert into database
        if enquiries_collection is not None:
            # Check if enquiry already exists for this mobile number and message ID to avoid duplicates
            existing_enquiry = enquiries_collection.find_one({
                'mobile_number': clean_number,
                'whatsapp_message_id': message_id
            })
            
            if existing_enquiry:
                logger.info(f"📝 Enquiry already exists for message ID {message_id}, skipping creation")
                return jsonify({
                    'success': True,
                    'message': 'Enquiry already exists',
                    'enquiry_id': str(existing_enquiry['_id'])
                }), 200
            
            # Insert new enquiry
            result = enquiries_collection.insert_one(new_enquiry)
            new_enquiry['_id'] = str(result.inserted_id)
            
            logger.info(f"✅ New WhatsApp enquiry created successfully:")
            logger.info(f"   Enquiry ID: {new_enquiry['_id']}")
            logger.info(f"   Customer: {display_name}")
            logger.info(f"   Mobile: {clean_number}")
            logger.info(f"   WhatsApp Name: {sender_name}")
            
            # Emit socket event to notify frontend with comprehensive status
            try:
                from app import socketio
                
                # Determine the status message based on data availability
                if sender_name and sender_name.strip() and sender_name.strip() != 'null':
                    status_message = "✅ SUCCESS: WhatsApp enquiry created with full details"
                    status_type = "success"
                else:
                    status_message = "⚠️ PARTIAL SUCCESS: Enquiry created but sender name not available (Free GreenAPI plan limitation)"
                    status_type = "warning"
                
                # Serialize the enquiry for socket emission
                socket_data = {
                    '_id': new_enquiry['_id'],
                    'wati_name': new_enquiry['wati_name'],
                    'user_name': new_enquiry['user_name'],
                    'mobile_number': new_enquiry['mobile_number'],
                    'comments': new_enquiry['comments'],
                    'staff': new_enquiry['staff'],
                    'source': new_enquiry['source'],
                    'whatsapp_sender_name': new_enquiry['whatsapp_sender_name'],
                    'created_at': new_enquiry['created_at'].isoformat(),
                    'date': new_enquiry['date'].isoformat()
                }
                
                # Emit enquiry creation event
                socketio.emit('new_enquiry', socket_data)
                
                # Emit status notification
                status_notification = {
                    'type': 'webhook_status',
                    'status': status_type,
                    'message': status_message,
                    'details': {
                        'mobile_number': clean_number,
                        'sender_name_available': bool(sender_name and sender_name.strip() and sender_name.strip() != 'null'),
                        'greenapi_plan': 'free',
                        'whatsapp_account_type': 'normal',
                        'enquiry_created': True,
                        'enquiry_id': new_enquiry['_id']
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                socketio.emit('webhook_notification', status_notification)
                logger.info(f"📡 Socket events emitted for new WhatsApp enquiry with status: {status_type}")
                
            except Exception as socket_error:
                logger.error(f"❌ Error emitting socket event: {socket_error}")
                
                # Even if socket fails, emit a basic notification
                try:
                    from app import socketio
                    error_notification = {
                        'type': 'webhook_status',
                        'status': 'error',
                        'message': f"❌ ERROR: Enquiry created but notification failed: {str(socket_error)}",
                        'details': {
                            'mobile_number': clean_number,
                            'enquiry_created': True,
                            'notification_error': str(socket_error)
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    socketio.emit('webhook_notification', error_notification)
                except:
                    pass  # If even this fails, just log it
            
            return jsonify({
                'success': True,
                'message': 'WhatsApp enquiry created successfully',
                'enquiry_id': new_enquiry['_id'],
                'customer_name': display_name,
                'mobile_number': clean_number,
                'whatsapp_name': sender_name
            }), 200
        else:
            logger.error("❌ Database not available for enquiry creation")
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'WhatsApp webhook failed: {str(e)}'}), 500

@enquiry_bp.route('/whatsapp/public-send', methods=['POST'])
def public_send_whatsapp():
    """Send WhatsApp message for public users without authentication"""
    try:
        data = request.get_json()
        
        if not data or 'mobile_number' not in data:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        mobile_number = data['mobile_number']
        message_type = data.get('message_type', 'new_enquiry')
        wati_name = data.get('wati_name', 'Public User')
        
        logger.info(f"📱 Public WhatsApp request - Mobile: {mobile_number}, Type: {message_type}")
        
        # Create enquiry data
        enquiry_data = {
            'wati_name': wati_name,
            'mobile_number': mobile_number,
            'comments': 'New Enquiry - Interested'
        }
        
        # Check if WhatsApp service is available
        if whatsapp_service is None or not whatsapp_service.api_available:
            # If service is not available, create the enquiry record anyway
            # and return success so the frontend can redirect to WhatsApp
            logger.info("WhatsApp service not available, creating enquiry record only")
            
            # Create a new enquiry record
            new_enquiry = {
                'date': datetime.utcnow(),
                'wati_name': wati_name,
                'mobile_number': mobile_number,
                'gst': '',
                'business_type': '',
                'business_nature': '',
                'staff': '',
                'comments': 'New Enquiry - Interested',
                'additional_comments': '',
                'whatsapp_status': 'pending',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Insert into database
            if enquiries_collection is not None:
                result = enquiries_collection.insert_one(new_enquiry)
                new_enquiry['_id'] = str(result.inserted_id)
                
                logger.info(f"✅ New public enquiry created: {new_enquiry['_id']}")
                
                # Emit socket event to notify frontend
                try:
                    from app import socketio
                    socketio.emit('new_enquiry', new_enquiry)
                except Exception as socket_error:
                    logger.error(f"❌ Error emitting socket event: {socket_error}")
                
                return jsonify({
                    'success': True,
                    'message': 'Enquiry created successfully',
                    'enquiry_id': new_enquiry['_id']
                }), 200
            else:
                logger.error("❌ Database not available for enquiry creation")
                return jsonify({
                    'success': False,
                    'error': 'Database not available'
                }), 500
        else:
            # If service is available, send the message and create the enquiry
            logger.info("WhatsApp service available, sending message and creating enquiry")
            
            # Send the message
            result = whatsapp_service.send_message(mobile_number, 'New Enquiry - Interested')
            if result['success']:
                logger.info(f"✅ Message sent to {mobile_number}")
                
                # Create a new enquiry record
                new_enquiry = {
                    'date': datetime.utcnow(),
                    'wati_name': wati_name,
                    'mobile_number': mobile_number,
                    'gst': '',
                    'business_type': '',
                    'business_nature': '',
                    'staff': '',
                    'comments': 'New Enquiry - Interested',
                    'additional_comments': '',
                    'whatsapp_status': 'sent',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                # Insert into database
                if enquiries_collection is not None:
                    result = enquiries_collection.insert_one(new_enquiry)
                    new_enquiry['_id'] = str(result.inserted_id)
                    
                    logger.info(f"✅ New public enquiry created: {new_enquiry['_id']}")
                    
                    # Emit socket event to notify frontend
                    try:
                        from app import socketio
                        socketio.emit('new_enquiry', new_enquiry)
                    except Exception as socket_error:
                        logger.error(f"❌ Error emitting socket event: {socket_error}")
                    
                    return jsonify({
                        'success': True,
                        'message': 'Enquiry created successfully',
                        'enquiry_id': new_enquiry['_id']
                    }), 200
                else:
                    logger.error("❌ Database not available for enquiry creation")
                    return jsonify({
                        'success': False,
                        'error': 'Database not available'
                    }), 500
            else:
                logger.error(f"❌ Failed to send message to {mobile_number}: {result.get('error')}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to send message: {result.get("error")}'
                }), 500
            
    except Exception as e:
        logger.error(f"❌ Error sending public WhatsApp message: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error sending message: {str(e)}'
        }), 500

@enquiry_bp.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    try:
        data = request.get_json()
        logger.info(f"Received WhatsApp webhook data: {data}")
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Invalid webhook data'}), 400
        
        message = data['message']
        chat_id = data['chatId']
        message_text = message.get('text', '')
        sender_name = data.get('senderName', '')
        display_name = sender_name or chat_id
        
        # Check if this is one of our reply options
        if _is_reply_option(message_text):
            logger.info(f"🔄 Processing reply option from {data.get('senderName', '') or chat_id}: {message_text}")
            # Send appropriate response
            response_text = _get_reply_response(message_text)
            if whatsapp_service and whatsapp_service.api_available:
                # Use the proper method to send the message
                logger.info(f"📤 Sending reply message: {response_text}")
                result = whatsapp_service.send_message(chat_id, response_text)
                if result['success']:
                    logger.info(f"✅ Reply sent for option '{message_text}' to {chat_id}")
                    # Emit success notification
                    try:
                        from app import socketio
                        notification = {
                            'type': 'webhook_status',
                            'status': 'success',
                            'message': f"✅ WhatsApp reply sent successfully for '{message_text}'",
                            'details': {
                                'message_type': 'reply_option',
                                'option_selected': message_text,
                                'recipient': chat_id,
                                'message_id': result.get('message_id', 'unknown')
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        socketio.emit('webhook_notification', notification)
                    except Exception as socket_error:
                        logger.error(f"❌ Error emitting socket event: {socket_error}")
                else:
                    logger.error(f"❌ Failed to send reply for option '{message_text}' to {chat_id}: {result.get('error')}")
                    # Log additional error details
                    logger.error(f"❌ Error details: {result}")
                    
                    # Emit error notification
                    try:
                        from app import socketio
                        notification = {
                            'type': 'webhook_status',
                            'status': 'error',
                            'message': f"❌ Failed to send WhatsApp reply for '{message_text}': {result.get('error', 'Unknown error')}",
                            'details': {
                                'message_type': 'reply_option',
                                'option_selected': message_text,
                                'recipient': chat_id,
                                'error': result.get('error', 'Unknown error')
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        socketio.emit('webhook_notification', notification)
                    except Exception as socket_error:
                        logger.error(f"❌ Error emitting socket event: {socket_error}")
                    
                    # Check for quota exceeded error
                    error_msg = result.get('error', '').lower()
                    status_code = result.get('status_code', 0)
                    
                    if 'quota exceeded' in error_msg or 'monthly quota' in error_msg or status_code == 466:
                        logger.warning(f"⚠️ GreenAPI quota exceeded when sending reply to {chat_id}")
                        # Still return success to the webhook (we don't want to cause webhook errors)
                        # but log the quota issue
            else:
                logger.error("❌ WhatsApp service not available")
                # Emit service unavailable notification
                try:
                    from app import socketio
                    notification = {
                        'type': 'webhook_status',
                        'status': 'error',
                        'message': "❌ WhatsApp service not available - Check GreenAPI configuration",
                        'details': {
                            'message_type': 'reply_option',
                            'option_selected': message_text,
                            'recipient': chat_id,
                            'error': 'Service not available'
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    socketio.emit('webhook_notification', notification)
                except Exception as socket_error:
                    logger.error(f"❌ Error emitting socket event: {socket_error}")
            return jsonify({
                'success': True,
                'message': 'Reply option processed'
            }), 200
        
        # Create enquiry data
        enquiry_data = {
            'wati_name': sender_name,
            'user_name': sender_name,
            'mobile_number': chat_id,
            'comments': message_text,
            'staff': '',
            'source': 'WhatsApp',
            'whatsapp_sender_name': sender_name,
            'created_at': datetime.utcnow(),
            'date': datetime.utcnow()
        }
        
        # Check if database is available
        if enquiries_collection is not None:
            try:
                # Insert into database
                result = enquiries_collection.insert_one(enquiry_data)
                new_enquiry = result.inserted_id
                
                logger.info(f"✅ New WhatsApp enquiry created: {new_enquiry}")
                
                # Emit socket event to notify frontend
                try:
                    from app import socketio
                    socketio.emit('new_enquiry', enquiry_data)
                except Exception as socket_error:
                    logger.error(f"❌ Error emitting socket event: {socket_error}")
                
                # Determine the status message based on data availability
                if sender_name and sender_name.strip() and sender_name.strip() != 'null':
                    status_message = "✅ SUCCESS: WhatsApp enquiry created with full details"
                    status_type = "success"
                else:
                    status_message = "⚠️ PARTIAL SUCCESS: Enquiry created but sender name not available (Free GreenAPI plan limitation)"
                    status_type = "warning"
                
                # Serialize the enquiry for socket emission
                socket_data = {
                    '_id': new_enquiry['_id'],
                    'wati_name': new_enquiry['wati_name'],
                    'user_name': new_enquiry['user_name'],
                    'mobile_number': new_enquiry['mobile_number'],
                    'comments': new_enquiry['comments'],
                    'staff': new_enquiry['staff'],
                    'source': new_enquiry['source'],
                    'whatsapp_sender_name': new_enquiry['whatsapp_sender_name'],
                    'created_at': new_enquiry['created_at'].isoformat(),
                    'date': new_enquiry['date'].isoformat()
                }
                
                # Emit enquiry creation event
                socketio.emit('new_enquiry', socket_data)
                
                # Emit status notification
                status_notification = {
                    'type': 'webhook_status',
                    'status': status_type,
                    'message': status_message,
                    'details': {
                        'mobile_number': clean_number,
                        'sender_name_available': bool(sender_name and sender_name.strip() and sender_name.strip() != 'null'),
                        'greenapi_plan': 'free',
                        'whatsapp_account_type': 'normal',
                        'enquiry_created': True,
                        'enquiry_id': new_enquiry['_id']
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                socketio.emit('webhook_notification', status_notification)
                logger.info(f"📡 Socket events emitted for new WhatsApp enquiry with status: {status_type}")
                
            except Exception as socket_error:
                logger.error(f"❌ Error emitting socket event: {socket_error}")
                
                # Even if socket fails, emit a basic notification
                try:
                    from app import socketio
                    error_notification = {
                        'type': 'webhook_status',
                        'status': 'error',
                        'message': f"❌ ERROR: Enquiry created but notification failed: {str(socket_error)}",
                        'details': {
                            'mobile_number': clean_number,
                            'enquiry_created': True,
                            'notification_error': str(socket_error)
                        },
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    socketio.emit('webhook_notification', error_notification)
                except:
                    pass  # If even this fails, just log it
            
            return jsonify({
                'success': True,
                'message': 'WhatsApp enquiry created successfully',
                'enquiry_id': new_enquiry['_id'],
                'customer_name': display_name,
                'mobile_number': clean_number,
                'whatsapp_name': sender_name
            }), 200
        else:
            logger.error("❌ Database not available for enquiry creation")
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500

    # If service is available, send the message
    result = whatsapp_service.send_enquiry_message(enquiry_data, message_type)

    logger.info(f"Public WhatsApp send result: {result}")

    # Create a new enquiry record regardless of WhatsApp send result
    new_enquiry = {
        'date': datetime.utcnow(),
        'wati_name': wati_name,
        'mobile_number': mobile_number,
        'gst': '',
        'business_type': '',
        'business_nature': '',
        'staff': '',
        'comments': 'New Enquiry - Interested',
        'additional_comments': '',
        'whatsapp_status': 'sent' if result['success'] else 'failed',
        'whatsapp_message_id': result.get('message_id', ''),
        'whatsapp_error': result.get('error', '') if not result['success'] else '',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    # Insert into database
    if enquiries_collection is not None:
        db_result = enquiries_collection.insert_one(new_enquiry)
        new_enquiry['_id'] = str(db_result.inserted_id)

        logger.info(f"✅ New public enquiry created: {new_enquiry['_id']}")

        # Emit socket event to notify frontend
        try:
            from app import socketio
            socketio.emit('new_enquiry', new_enquiry)
        except Exception as socket_error:
            logger.error(f"❌ Error emitting socket event: {socket_error}")
    else:
        logger.error("❌ Database not available for enquiry creation")

    if result['success']:
        return jsonify({
            'success': True,
            'message': 'WhatsApp message sent and enquiry created successfully',
            'message_id': result.get('message_id'),
            'enquiry_id': new_enquiry['_id'] if '_id' in new_enquiry else None,
            'mobile_number': mobile_number,
            'message_type': message_type,
            'whatsapp_redirect': True
        }), 200
    else:
        # Even if WhatsApp send failed, we still created the enquiry
        return jsonify({
            'success': True,
            'message': 'Enquiry created successfully (WhatsApp message may have failed)',
            'enquiry_id': new_enquiry['_id'] if '_id' in new_enquiry else None,
            'mobile_number': mobile_number,
            'message_type': message_type,
            'whatsapp_error': result.get('error', ''),
            'whatsapp_redirect': True
        }), 200

except Exception as e:
    logger.error(f"Error in public WhatsApp send: {str(e)}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({'error': f'Public WhatsApp send failed: {str(e)}'}), 500
