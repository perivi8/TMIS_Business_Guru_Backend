from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
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
    except Exception as e:
        logger.error(f"Error parsing date {date_input}: {e}")
        return datetime.now()

@enquiry_bp.route('/enquiries', methods=['GET'])
@jwt_required()
def get_all_enquiries():
    """Get all enquiries with optional filtering"""
    try:
        # Check if database is available
        if db is None or enquiries_collection is None:
            return jsonify({
                'error': 'Database not available',
                'enquiries': []
            }), 500
        
        # Get JWT claims for user info
        current_user_id = get_jwt_identity()
        
        # Get query parameters for filtering
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        staff_filter = request.args.get('staff', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = {}
        
        # Add staff filter if provided
        if staff_filter:
            query['staff'] = staff_filter
        
        # Add date range filter if provided
        if date_from or date_to:
            date_query = {}
            if date_from:
                try:
                    date_query['$gte'] = parse_date_safely(date_from)
                except:
                    pass
            if date_to:
                try:
                    date_query['$lte'] = parse_date_safely(date_to)
                except:
                    pass
            if date_query:
                query['date'] = date_query
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get total count for pagination
        total_count = enquiries_collection.count_documents(query)
        
        # Get enquiries with pagination and sorting (newest first)
        enquiries_cursor = enquiries_collection.find(query).sort('date', -1).skip(skip).limit(limit)
        enquiries = list(enquiries_cursor)
        
        # Check staff assignment lock status
        staff_lock_status = check_staff_assignment_lock_status()
        
        # Serialize enquiries for JSON response and add staff lock info
        serialized_enquiries = []
        for enquiry in enquiries:
            serialized_enquiry = serialize_enquiry(enquiry)
            
            # Add comprehensive staff dropdown status for frontend
            dropdown_status = get_enquiry_staff_dropdown_status(enquiry, staff_lock_status)
            
            # Add all status fields for frontend use
            serialized_enquiry['staff_assignment_locked'] = staff_lock_status['locked']
            serialized_enquiry['can_assign_staff'] = dropdown_status['can_assign']
            serialized_enquiry['staff_dropdown_enabled'] = dropdown_status['enabled']
            serialized_enquiry['staff_dropdown_clickable'] = dropdown_status['clickable']
            serialized_enquiry['staff_dropdown_reason'] = dropdown_status['reason']
            serialized_enquiry['staff_dropdown_ui_state'] = dropdown_status['ui_state']
            
            # Add enquiry age info for frontend reference
            enquiry_date = enquiry.get('date', datetime.utcnow())
            if isinstance(enquiry_date, str):
                enquiry_date = parse_date_safely(enquiry_date)
            
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            serialized_enquiry['is_old_enquiry'] = enquiry_date < one_day_ago
            serialized_enquiry['enquiry_age_days'] = (datetime.utcnow() - enquiry_date).days
            
            serialized_enquiries.append(serialized_enquiry)
        
        logger.info(f"Retrieved {len(serialized_enquiries)} enquiries for user {current_user_id}")
        
        return jsonify({
            'enquiries': serialized_enquiries,
            'staff_lock_status': staff_lock_status,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            },
            'filters': {
                'staff': staff_filter,
                'date_from': date_from,
                'date_to': date_to
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting enquiries: {str(e)}")
        return jsonify({
            'error': f'Failed to get enquiries: {str(e)}',
            'enquiries': []
        }), 500

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

@enquiry_bp.route('/enquiries/public', methods=['POST'])
def create_public_enquiry():
    """Create a new enquiry from public form (no JWT required)"""
    try:
        # Check if database is available
        if db is None or enquiries_collection is None:
            return jsonify({
                'error': 'Database not available'
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract enquiry data
        wati_name = data.get('wati_name', '')
        mobile_number = data.get('mobile_number', '')
        business_type = data.get('business_type', '')
        business_nature = data.get('business_nature', '')
        gst = data.get('gst', '')
        
        # Validate required fields
        if not wati_name or not mobile_number:
            return jsonify({'error': 'Name and mobile number are required'}), 400
        
        # Clean mobile number
        clean_number = ''.join(filter(str.isdigit, mobile_number))
        
        # Create enquiry record
        new_enquiry = {
            'date': datetime.utcnow(),
            'wati_name': wati_name,
            'mobile_number': clean_number,
            'secondary_mobile_number': None,
            'gst': gst,
            'gst_status': '',
            'business_type': business_type,
            'business_nature': business_nature,
            'staff': 'Public Form',
            'comments': 'New Enquiry - Public Form',
            'additional_comments': '',
            'whatsapp_status': 'pending',
            'whatsapp_sent': False,
            'source': 'public_form',
            'staff_locked': False,  # Keep unlocked for public forms
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert into database
        result = enquiries_collection.insert_one(new_enquiry)
        new_enquiry['_id'] = str(result.inserted_id)
        
        logger.info(f"Created public enquiry for {wati_name} ({clean_number})")
        
        # Send WhatsApp welcome message
        whatsapp_result = None
        try:
            if whatsapp_service and whatsapp_service.api_available:
                logger.info(f"Attempting to send WhatsApp welcome message to {clean_number}")
                
                # Send the welcome message using the enquiry message function
                # For public form enquiries, use the template without 'Get Loan' option
                whatsapp_result = whatsapp_service.send_enquiry_message(new_enquiry, 'new_enquiry_public_form')
                
                if whatsapp_result['success']:
                    logger.info(f"WhatsApp welcome message sent successfully to {clean_number}")
                    # Update enquiry to mark welcome message as sent
                    new_enquiry['whatsapp_sent'] = True
                    enquiries_collection.update_one(
                        {'_id': result.inserted_id},
                        {'$set': {'whatsapp_sent': True, 'updated_at': datetime.utcnow()}}
                    )
                else:
                    error_msg = whatsapp_result.get('error', 'Unknown error')
                    logger.error(f"Failed to send WhatsApp welcome message to {clean_number}: {error_msg}")
            else:
                logger.error("WhatsApp service is not available")
                whatsapp_result = {
                    'success': False,
                    'error': 'WhatsApp service not available - Check GreenAPI configuration'
                }
        except Exception as whatsapp_error:
            logger.error(f"Error sending WhatsApp welcome message: {str(whatsapp_error)}")
            whatsapp_result = {
                'success': False,
                'error': f'Error sending WhatsApp message: {str(whatsapp_error)}'
            }
        
        return jsonify({
            'success': True,
            'message': 'Enquiry created successfully',
            'enquiry_id': str(result.inserted_id),
            'whatsapp_sent': whatsapp_result['success'] if whatsapp_result else False,
            'whatsapp_error': whatsapp_result.get('error') if whatsapp_result else None
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating public enquiry: {str(e)}")
        return jsonify({
            'error': f'Failed to create enquiry: {str(e)}'
        }), 500

@enquiry_bp.route('/enquiries/whatsapp/public-send', methods=['POST'])
def send_public_whatsapp():
    """Send WhatsApp message from public form (no JWT required)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        mobile_number = data.get('mobile_number', '')
        wati_name = data.get('wati_name', 'User')
        
        if not mobile_number:
            return jsonify({'error': 'Mobile number is required'}), 400
        
        # Clean mobile number
        clean_number = ''.join(filter(str.isdigit, mobile_number))
        
        # Check if WhatsApp service is available
        if not whatsapp_service or not whatsapp_service.api_available:
            return jsonify({
                'success': False,
                'error': 'WhatsApp service not available'
            }), 503
        
        # Create welcome message
        message = f"""Hello {wati_name}! 👋

Welcome to Business Guru! We're delighted to have you with us. 

At Business Guru, we specialize in providing collateral-free loans to help businesses like yours grow and thrive. Our team of financial experts is ready to assist you with personalized loan solutions tailored to your business needs.

We'll be contacting you shortly to discuss your requirements in detail and guide you through our simple application process.

Please reply with one of these options:
• Get Loan
• Check Eligibility  
• More Details

Thank you for choosing Business Guru! 🚀"""
        
        # Send WhatsApp message
        chat_id = f"{clean_number}@c.us"
        result = whatsapp_service.send_message(chat_id, message)
        
        if result['success']:
            logger.info(f"Public WhatsApp message sent to {clean_number}")
            return jsonify({
                'success': True,
                'message': 'WhatsApp message sent successfully',
                'message_id': result.get('message_id', '')
            }), 200
        else:
            logger.error(f"Failed to send public WhatsApp message to {clean_number}: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to send message')
            }), 500
            
    except Exception as e:
        logger.error(f"Error sending public WhatsApp message: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to send message: {str(e)}'
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
        
        if is_reply_option:
            logger.info(f"🔄 Processing reply option from {sender_name or chat_id}: {message_text}")
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
            'staff_locked': False,  # Keep unlocked for WhatsApp forms
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
            
            # Send welcome message
            if whatsapp_service and whatsapp_service.api_available:
                try:
                    logger.info(f"📤 Sending welcome message to {display_name} ({clean_number})...")
                    welcome_message_result = whatsapp_service.send_enquiry_message(new_enquiry, 'new_enquiry')
                    if welcome_message_result['success']:
                        logger.info(f"✅ Welcome message sent successfully to {chat_id}")
                        logger.info(f"   Message ID: {welcome_message_result.get('message_id', 'N/A')}")
                        # Update enquiry to mark welcome message as sent
                        new_enquiry['whatsapp_sent'] = True
                        enquiries_collection.update_one(
                            {'_id': result.inserted_id},
                            {'$set': {'whatsapp_sent': True, 'updated_at': datetime.utcnow()}}
                        )
                        
                        # Emit success notification
                        try:
                            from app import socketio
                            notification = {
                                'type': 'webhook_status',
                                'status': 'success',
                                'message': f"✅ WhatsApp welcome message sent successfully to {display_name}",
                                'details': {
                                    'message_type': 'welcome_message',
                                    'recipient': chat_id,
                                    'message_id': welcome_message_result.get('message_id', 'unknown'),
                                    'enquiry_id': str(result.inserted_id)
                                },
                                'timestamp': datetime.utcnow().isoformat()
                            }
                            socketio.emit('webhook_notification', notification)
                        except Exception as socket_error:
                            logger.error(f"❌ Error emitting socket event: {socket_error}")
                    else:
                        error_msg = welcome_message_result.get('error', 'Unknown error')
                        logger.error(f"❌ Failed to send welcome message to {chat_id}: {error_msg}")
                        
                        # Check for quota exceeded error
                        quota_exceeded = (
                            welcome_message_result.get('status_code') == 466 or 
                            welcome_message_result.get('quota_exceeded') or 
                            'quota exceeded' in error_msg.lower() or 
                            'monthly quota' in error_msg.lower()
                        )
                        
                        if quota_exceeded:
                            logger.warning(f"🚨 GreenAPI QUOTA LIMIT REACHED for {chat_id}")
                            logger.warning(f"   Error details: {error_msg}")
                            logger.warning(f"   Test number {welcome_message_result.get('working_test_number', '8106811285')} still works")
                            logger.warning(f"   Solution: Upgrade at {welcome_message_result.get('upgrade_url', 'https://console.green-api.com')}")
                            
                            # Emit quota exceeded notification
                            try:
                                from app import socketio
                                notification = {
                                    'type': 'webhook_status',
                                    'status': 'warning',
                                    'message': f"⚠️ GreenAPI quota limit reached! Welcome message not sent to {display_name}",
                                    'details': {
                                        'message_type': 'welcome_message',
                                        'recipient': chat_id,
                                        'error': error_msg,
                                        'quota_exceeded': True,
                                        'working_test_number': welcome_message_result.get('working_test_number', '8106811285'),
                                        'upgrade_url': welcome_message_result.get('upgrade_url', 'https://console.green-api.com'),
                                        'enquiry_id': str(result.inserted_id)
                                    },
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                socketio.emit('webhook_notification', notification)
                            except Exception as socket_error:
                                logger.error(f"❌ Error emitting socket event: {socket_error}")
                        else:
                            # Emit general error notification
                            try:
                                from app import socketio
                                notification = {
                                    'type': 'webhook_status',
                                    'status': 'error',
                                    'message': f"❌ Failed to send WhatsApp welcome message to {display_name}: {error_msg}",
                                    'details': {
                                        'message_type': 'welcome_message',
                                        'recipient': chat_id,
                                        'error': error_msg,
                                        'enquiry_id': str(result.inserted_id)
                                    },
                                    'timestamp': datetime.utcnow().isoformat()
                                }
                                socketio.emit('webhook_notification', notification)
                            except Exception as socket_error:
                                logger.error(f"❌ Error emitting socket event: {socket_error}")
                except Exception as welcome_error:
                    logger.error(f"❌ Error sending welcome message: {str(welcome_error)}")
                    # Emit exception notification
                    try:
                        from app import socketio
                        notification = {
                            'type': 'webhook_status',
                            'status': 'error',
                            'message': f"❌ Exception while sending WhatsApp welcome message to {display_name}: {str(welcome_error)}",
                            'details': {
                                'message_type': 'welcome_message',
                                'recipient': chat_id,
                                'error': str(welcome_error),
                                'enquiry_id': str(result.inserted_id)
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        socketio.emit('webhook_notification', notification)
                    except Exception as socket_error:
                        logger.error(f"❌ Error emitting socket event: {socket_error}")
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
            
            # Emit database error notification
            try:
                from app import socketio
                error_notification = {
                    'type': 'webhook_status',
                    'status': 'error',
                    'message': "❌ DATABASE ERROR: Cannot create enquiry - database connection failed",
                    'details': {
                        'mobile_number': clean_number,
                        'sender_name': sender_name,
                        'enquiry_created': False,
                        'error_type': 'database_connection'
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                socketio.emit('webhook_notification', error_notification)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': 'Database not available'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error creating enquiry: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error creating enquiry: {str(e)}'
        }), 500

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
        
        # Check if staff assignment is allowed based on business rules
        if 'staff' in data:
            new_staff = data['staff']
            current_staff = existing_enquiry.get('staff', '')
            is_public_or_whatsapp_form = current_staff in ['Public Form', 'WhatsApp Form', 'WhatsApp Bot']
            
            # If trying to assign actual staff (not clearing or public/whatsapp forms)
            if new_staff and new_staff.strip() not in ['', 'Public Form', 'WhatsApp Form', 'WhatsApp Bot']:
                # Check if staff assignment is allowed for this enquiry
                if not can_assign_staff_to_enquiry(existing_enquiry):
                    staff_lock_status = check_staff_assignment_lock_status()
                    if staff_lock_status['locked']:
                        return jsonify({
                            'error': 'Staff assignment is currently locked. Please assign staff to old enquiries first.',
                            'reason': staff_lock_status['reason'],
                            'staff_lock_status': staff_lock_status
                        }), 400
            
            # Check if staff is already assigned and locked (existing logic)
            if existing_enquiry.get('staff_locked', False) and not is_public_or_whatsapp_form:
                old_staff = existing_enquiry.get('staff', '')
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
        
        # Check if staff is being assigned (not Public Form or WhatsApp Form)
        # If so, lock the staff assignment
        if 'staff' in data:
            new_staff = data['staff']
            if new_staff and new_staff.strip() not in ['Public Form', 'WhatsApp Form', 'WhatsApp Bot', '']:
                # Lock the staff assignment
                update_doc['staff_locked'] = True
                logger.info(f"Staff assigned: {new_staff}. Locking staff assignment.")
                
                # Log staff assignment for tracking
                logger.info(f"Staff assignment completed for enquiry {enquiry_id}. This may unlock staff assignments for new enquiries.")
            elif new_staff and new_staff.strip() in ['Public Form', 'WhatsApp Form', 'WhatsApp Bot']:
                # Keep unlocked for public/whatsapp forms
                update_doc['staff_locked'] = False
                logger.info(f"Public/WhatsApp form staff assigned: {new_staff}. Keeping unlocked.")
        
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
                            
                            # Staff assignment completed - this may unlock staff assignments for other enquiries
                            logger.info(f"Staff assignment completed for enquiry {enquiry_id} - checking if this unlocks other assignments")
                            
                            # Check updated lock status after this assignment
                            updated_lock_status = check_staff_assignment_lock_status()
                            if not updated_lock_status['locked']:
                                logger.info(f"Staff assignments are now unlocked for new enquiries due to this assignment")
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

@enquiry_bp.route('/enquiries/staff-lock-status', methods=['GET'])
@jwt_required()
def get_staff_lock_status():
    """Get current staff assignment lock status"""
    try:
        # Check if database is available
        if db is None or enquiries_collection is None:
            return jsonify({'error': 'Database not available'}), 500
        
        staff_lock_status = check_staff_assignment_lock_status()
        return jsonify(staff_lock_status), 200
        
    except Exception as e:
        logger.error(f"Error getting staff lock status: {str(e)}")
        return jsonify({'error': f'Failed to get staff lock status: {str(e)}'}), 500

def check_staff_assignment_lock_status():
    """Check if staff assignments should be locked based on business rules"""
    try:
        if db is None or enquiries_collection is None:
            return {
                'locked': False,
                'reason': 'Database not available',
                'unassigned_old_enquiries': 0,
                'assigned_enquiries': 0
            }
        
        # Count old enquiries without staff assignment
        # Consider enquiries older than 1 day as "old"
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        
        old_unassigned_query = {
            'date': {'$lt': one_day_ago},
            '$or': [
                {'staff': {'$exists': False}},
                {'staff': None},
                {'staff': ''},
                {'staff': 'Public Form'},
                {'staff': 'WhatsApp Bot'},
                {'staff': 'WhatsApp Form'}
            ]
        }
        
        unassigned_old_count = enquiries_collection.count_documents(old_unassigned_query)
        
        # Count enquiries with actual staff assignments (not public/whatsapp forms)
        assigned_query = {
            'staff': {
                '$exists': True,
                '$nin': [None, '', 'Public Form', 'WhatsApp Bot', 'WhatsApp Form']
            }
        }
        
        assigned_count = enquiries_collection.count_documents(assigned_query)
        
        # Staff assignments are locked if there are old unassigned enquiries
        # and no staff has been assigned to any enquiry yet
        locked = unassigned_old_count > 0 and assigned_count == 0
        
        reason = ''
        if locked:
            reason = f'Staff assignments locked: {unassigned_old_count} old enquiries without staff assignment. Assign staff to an old enquiry first to unlock.'
        elif unassigned_old_count > 0 and assigned_count > 0:
            reason = f'Staff assignments unlocked: {assigned_count} enquiries have staff assigned.'
        else:
            reason = 'No restrictions on staff assignments.'
        
        logger.info(f"Staff lock status: locked={locked}, old_unassigned={unassigned_old_count}, assigned={assigned_count}")
        
        return {
            'locked': locked,
            'reason': reason,
            'unassigned_old_enquiries': unassigned_old_count,
            'assigned_enquiries': assigned_count
        }
        
    except Exception as e:
        logger.error(f"Error checking staff lock status: {str(e)}")
        return {
            'locked': False,
            'reason': f'Error checking lock status: {str(e)}',
            'unassigned_old_enquiries': 0,
            'assigned_enquiries': 0
        }

def can_assign_staff_to_enquiry(enquiry, staff_lock_status=None):
    """Check if staff can be assigned to a specific enquiry"""
    try:
        if staff_lock_status is None:
            staff_lock_status = check_staff_assignment_lock_status()
        
        # If staff assignments are not locked globally, allow assignment
        if not staff_lock_status['locked']:
            return True
        
        # If locked, only allow assignment to old enquiries without staff
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        enquiry_date = enquiry.get('date', datetime.utcnow())
        
        # Convert string date to datetime if needed
        if isinstance(enquiry_date, str):
            enquiry_date = parse_date_safely(enquiry_date)
        
        is_old_enquiry = enquiry_date < one_day_ago
        current_staff = enquiry.get('staff', '')
        has_no_staff = current_staff in [None, '', 'Public Form', 'WhatsApp Bot', 'WhatsApp Form']
        
        can_assign = is_old_enquiry and has_no_staff
        
        logger.debug(f"Can assign staff to enquiry {enquiry.get('_id')}: {can_assign} (old: {is_old_enquiry}, no_staff: {has_no_staff})")
        
        return can_assign
        
    except Exception as e:
        logger.error(f"Error checking if can assign staff to enquiry: {str(e)}")
        return False

def get_enquiry_staff_dropdown_status(enquiry, staff_lock_status=None):
    """Get detailed staff dropdown status for frontend UI control"""
    try:
        if staff_lock_status is None:
            staff_lock_status = check_staff_assignment_lock_status()
        
        enquiry_date = enquiry.get('date', datetime.utcnow())
        if isinstance(enquiry_date, str):
            enquiry_date = parse_date_safely(enquiry_date)
        
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        is_old_enquiry = enquiry_date < one_day_ago
        
        current_staff = enquiry.get('staff', '')
        has_no_staff = current_staff in [None, '', 'Public Form', 'WhatsApp Bot', 'WhatsApp Form']
        
        # Determine dropdown status
        if not staff_lock_status['locked']:
            # No global lock - all dropdowns enabled
            return {
                'enabled': True,
                'clickable': True,
                'reason': 'Staff assignments are unlocked',
                'ui_state': 'enabled',
                'can_assign': True
            }
        else:
            # Global lock active
            if is_old_enquiry and has_no_staff:
                # Old enquiry without staff - dropdown ENABLED
                return {
                    'enabled': True,
                    'clickable': True,
                    'reason': 'Old enquiry - staff assignment required to unlock others',
                    'ui_state': 'enabled_priority',
                    'can_assign': True
                }
            elif is_old_enquiry and not has_no_staff:
                # Old enquiry with staff - dropdown ENABLED (can change)
                return {
                    'enabled': True,
                    'clickable': True,
                    'reason': 'Old enquiry with staff assigned',
                    'ui_state': 'enabled',
                    'can_assign': True
                }
            else:
                # New enquiry - dropdown COMPLETELY DISABLED
                return {
                    'enabled': False,
                    'clickable': False,
                    'reason': f'New enquiry - assign staff to {staff_lock_status["unassigned_old_enquiries"]} old enquiry(ies) first',
                    'ui_state': 'disabled_locked',
                    'can_assign': False
                }
        
    except Exception as e:
        logger.error(f"Error getting dropdown status: {str(e)}")
        return {
            'enabled': False,
            'clickable': False,
            'reason': f'Error: {str(e)}',
            'ui_state': 'disabled_error',
            'can_assign': False
        }

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
