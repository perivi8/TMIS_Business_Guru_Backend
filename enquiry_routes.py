from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        required_fields = ['wati_name', 'mobile_number', 'gst', 'staff', 'comments']
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
            
        if len(mobile_number) != 10:
            logger.error(f"Mobile number length is {len(mobile_number)}, expected 10: '{mobile_number}'")
            return jsonify({'error': f'Mobile number must be exactly 10 digits, got {len(mobile_number)}'}), 400
        
        # Validate secondary mobile number if provided
        secondary_mobile = data.get('secondary_mobile_number')
        if secondary_mobile is not None and secondary_mobile != '':
            secondary_mobile = str(secondary_mobile).strip()
            logger.info(f"Validating secondary mobile number: '{secondary_mobile}'")
            if not secondary_mobile.isdigit():
                logger.error(f"Secondary mobile number contains non-digits: '{secondary_mobile}'")
                return jsonify({'error': 'Secondary mobile number must contain only digits'}), 400
            if len(secondary_mobile) != 10:
                logger.error(f"Secondary mobile number length is {len(secondary_mobile)}, expected 10: '{secondary_mobile}'")
                return jsonify({'error': f'Secondary mobile number must be exactly 10 digits, got {len(secondary_mobile)}'}), 400
        else:
            logger.info("Secondary mobile number is null/empty - skipping validation")
            secondary_mobile = None  # Ensure it's None for database storage
        
        # Validate GST and GST status
        gst_value = str(data.get('gst')).strip()
        logger.info(f"GST value: '{gst_value}'")
        
        if gst_value not in ['Yes', 'No']:
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
        enquiry_data = {
            'wati_name': data.get('wati_name'),
            'user_name': data.get('user_name'),
            'mobile_number': mobile_number,
            'secondary_mobile_number': secondary_mobile,  # Use the validated variable
            'gst': gst_value,
            'gst_status': data.get('gst_status', ''),
            'business_type': data.get('business_type'),
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
        
        logger.info(f"Successfully created enquiry {result.inserted_id} for user {current_user}")
        return jsonify(serialized_enquiry), 201
        
    except Exception as e:
        logger.error(f"Error creating enquiry: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@enquiry_bp.route('/enquiries/<enquiry_id>', methods=['PUT'])
@jwt_required()
def update_enquiry(enquiry_id):
    """Update an existing enquiry"""
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
        
        # Validate mobile numbers if provided
        if 'mobile_number' in data:
            mobile_number = str(data['mobile_number']).strip()
            if not mobile_number.isdigit() or len(mobile_number) != 10:
                return jsonify({'error': 'Mobile number must be 10 digits'}), 400
        
        if 'secondary_mobile_number' in data and data['secondary_mobile_number']:
            secondary_mobile = str(data['secondary_mobile_number']).strip()
            if not secondary_mobile.isdigit() or len(secondary_mobile) != 10:
                return jsonify({'error': 'Secondary mobile number must be 10 digits'}), 400
        
        # Validate GST status if GST is Yes
        gst_value = str(data.get('gst', existing_enquiry.get('gst', ''))).strip()
        if gst_value == 'Yes' and not str(data.get('gst_status', existing_enquiry.get('gst_status', ''))).strip():
            return jsonify({'error': 'GST status is required when GST is Yes'}), 400
        
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
            'business_type', 'staff', 'comments', 'additional_comments'
        ]
        
        for field in updatable_fields:
            if field in data:
                if isinstance(data[field], str):
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
        
        logger.info(f"Updated enquiry {enquiry_id} by user {current_user}")
        return jsonify(serialized_enquiry), 200
        
    except Exception as e:
        logger.error(f"Error updating enquiry {enquiry_id}: {e}")
        return jsonify({'error': 'Failed to update enquiry'}), 500

@enquiry_bp.route('/enquiries/<enquiry_id>', methods=['DELETE'])
@jwt_required()
def delete_enquiry(enquiry_id):
    """Delete an enquiry"""
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
