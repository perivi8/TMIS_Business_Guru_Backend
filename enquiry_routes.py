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
        
        logger.info(f"Successfully created enquiry {result.inserted_id} for user {current_user}")
        return jsonify(serialized_enquiry), 201
        
    except Exception as e:
        logger.error(f"Error creating enquiry: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@enquiry_bp.route('/public/check-mobile', methods=['POST'])
def check_mobile_exists():
    """Check if mobile number already exists in enquiry records (public endpoint)"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        mobile_number = data.get('mobile_number', '').strip()
        
        if not mobile_number:
            return jsonify({'exists': False, 'message': 'No mobile number provided'}), 200
        
        # Check if mobile number exists in enquiry records
        existing_enquiry = enquiries_collection.find_one({
            '$or': [
                {'mobile_number': mobile_number},
                {'secondary_mobile_number': mobile_number}
            ]
        })
        
        if existing_enquiry:
            return jsonify({
                'exists': True,
                'message': 'This mobile number is already registered with us. Please use a different number or contact support if this is your number.'
            }), 200
        else:
            return jsonify({
                'exists': False,
                'message': 'Mobile number is available'
            }), 200
            
    except Exception as e:
        logger.error(f"Error checking mobile number: {str(e)}")
        return jsonify({'error': 'Failed to check mobile number'}), 500

@enquiry_bp.route('/public/enquiries', methods=['POST'])
def create_public_enquiry():
    """Create a new enquiry from public form (no authentication required)"""
    # Check if database is available
    if db is None or enquiries_collection is None:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json()
        logger.info(f"Received public enquiry data: {data}")
        
        # Validate required fields
        required_fields = ['wati_name', 'mobile_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate mobile number format
        mobile_number = str(data.get('mobile_number', '')).strip()
        if not mobile_number.isdigit() or len(mobile_number) < 10 or len(mobile_number) > 15:
            return jsonify({'error': 'Mobile number must be 10-15 digits'}), 400
        
        # Check for duplicate mobile number
        existing_enquiry = enquiries_collection.find_one({'mobile_number': mobile_number})
        if existing_enquiry:
            return jsonify({'error': 'Mobile number already exists. Please use a different number.'}), 400
        
        # Validate secondary mobile number if provided and check for duplicates
        secondary_mobile = data.get('secondary_mobile_number')
        if secondary_mobile and str(secondary_mobile).strip():
            secondary_mobile = str(secondary_mobile).strip()
            if not secondary_mobile.isdigit() or len(secondary_mobile) < 10 or len(secondary_mobile) > 15:
                return jsonify({'error': 'Secondary mobile number must be 10-15 digits'}), 400
            
            # Check if secondary mobile is same as primary
            if secondary_mobile == mobile_number:
                return jsonify({'error': 'Secondary mobile number cannot be same as primary mobile number'}), 400
            
            # Check for duplicate secondary mobile number
            existing_secondary = enquiries_collection.find_one({'mobile_number': secondary_mobile})
            if existing_secondary:
                return jsonify({'error': 'Secondary mobile number already exists. Please use a different number.'}), 400
            
            # Also check if secondary mobile exists as secondary mobile in other records
            existing_as_secondary = enquiries_collection.find_one({'secondary_mobile_number': secondary_mobile})
            if existing_as_secondary:
                return jsonify({'error': 'Secondary mobile number already exists. Please use a different number.'}), 400
        else:
            secondary_mobile = None
        
        # Handle GST and GST status properly
        gst_value = str(data.get('gst', '')).strip()
        gst_status_value = ''
        
        # Only save GST status if GST is selected (Yes or No)
        if gst_value in ['Yes', 'No']:
            if gst_value == 'Yes':
                gst_status_value = str(data.get('gst_status', '')).strip()
                if not gst_status_value:
                    return jsonify({'error': 'GST status is required when GST is Yes'}), 400
        else:
            gst_value = ''  # Set to empty if not selected
        
        # Create enquiry document
        enquiry = {
            'wati_name': data['wati_name'],
            'mobile_number': mobile_number,
            'secondary_mobile_number': secondary_mobile,
            'business_type': data.get('business_type', ''),
            'business_nature': data.get('business_nature', ''),
            'gst': gst_value,
            'gst_status': gst_status_value,
            'staff': data.get('staff', ''),
            'comments': data.get('comments', 'Public enquiry submission'),
            'additional_comments': data.get('additional_comments', ''),
            'status': 'Active',  # Default status for public enquiries
            'source': 'Public Form',  # Mark as public enquiry
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert into database
        result = enquiries_collection.insert_one(enquiry)
        
        # Retrieve the created enquiry for WhatsApp
        created_enquiry = enquiries_collection.find_one({'_id': result.inserted_id})
        
        # Prepare response
        enquiry['_id'] = str(result.inserted_id)
        enquiry['created_at'] = enquiry['created_at'].isoformat()
        enquiry['updated_at'] = enquiry['updated_at'].isoformat()
        
        # Send WhatsApp welcome message for public enquiry
        whatsapp_result = {'success': False, 'error': 'WhatsApp service not available'}
        try:
            if whatsapp_service is not None:
                logger.info(f"Attempting to send WhatsApp welcome message to {mobile_number} for public enquiry")
                
                # Send public enquiry welcome message
                whatsapp_result = whatsapp_service.send_enquiry_message(
                    created_enquiry, 
                    message_type='public_welcome'
                )
                
                if whatsapp_result['success']:
                    logger.info(f"WhatsApp welcome message sent successfully to {mobile_number}")
                    enquiry['whatsapp_sent'] = True
                    enquiry['whatsapp_message_id'] = whatsapp_result.get('message_id')
                    enquiry['whatsapp_notification'] = 'Welcome message sent via WhatsApp'
                else:
                    error_msg = whatsapp_result.get('error', 'Unknown error')
                    logger.warning(f"Failed to send WhatsApp message: {error_msg}")
                    enquiry['whatsapp_sent'] = False
                    enquiry['whatsapp_error'] = error_msg
            else:
                logger.warning("WhatsApp service is not initialized for public enquiry")
                enquiry['whatsapp_sent'] = False
                enquiry['whatsapp_error'] = "WhatsApp service not available"
                
        except Exception as whatsapp_error:
            logger.error(f"WhatsApp service error for public enquiry: {str(whatsapp_error)}")
            enquiry['whatsapp_sent'] = False
            enquiry['whatsapp_error'] = str(whatsapp_error)
        
        logger.info(f"Successfully created public enquiry {result.inserted_id}")
        return jsonify({
            'success': True,
            'message': 'Enquiry submitted successfully',
            '_id': str(result.inserted_id),
            'enquiry': enquiry,
            'whatsapp_result': whatsapp_result
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating public enquiry: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to submit enquiry: {str(e)}'}), 500

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
            if whatsapp_service is not None and 'comments' in data and updated_enquiry is not None:
                # Check if comments have changed
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
                else:
                    logger.info("Comments unchanged, skipping WhatsApp message")
            elif whatsapp_service is None:
                logger.error("WhatsApp service is not initialized")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "WhatsApp service not available - Check GreenAPI configuration"
            elif updated_enquiry is None:
                logger.error("Failed to retrieve updated enquiry")
                serialized_enquiry['whatsapp_sent'] = False
                serialized_enquiry['whatsapp_error'] = "Failed to retrieve updated enquiry"
            else:
                logger.info("No comments in update data, skipping WhatsApp message")
                
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
