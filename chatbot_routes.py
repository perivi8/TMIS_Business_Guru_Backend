from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import re
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini Chatbot Service
try:
    from gemini_chatbot_service import gemini_chatbot_service
    CHATBOT_SERVICE_AVAILABLE = True
    logger.info("✅ Gemini Chatbot Service imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import Gemini Chatbot Service: {e}")
    CHATBOT_SERVICE_AVAILABLE = False
    gemini_chatbot_service = None

# Create Blueprint
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chatbot/chat', methods=['POST'])
@jwt_required()
def chat():
    """Main chatbot endpoint for handling user queries"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service is not available'
            }), 503
        
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        # Get current user identity
        current_user = get_jwt_identity()
        logger.info(f"Chatbot query from user {current_user}: {user_message}")
        
        # Analyze the query to determine if it's a specific lookup
        query_analysis = analyze_query(user_message)
        
        if query_analysis['type'] == 'specific_query':
            response = gemini_chatbot_service.process_specific_query(
                query_analysis['query_type'], 
                query_analysis['parameters']
            )
        else:
            # General AI response
            context_type = query_analysis.get('context_type')
            response = gemini_chatbot_service.generate_response(user_message, context_type)
        
        return jsonify({
            'success': True,
            'response': response,
            'query_type': query_analysis.get('query_type', 'general'),
            'timestamp': query_analysis.get('timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error in chatbot endpoint: {e}")
        return jsonify({
            'success': False,
            'error': f'An error occurred while processing your request: {str(e)}'
        }), 500

@chatbot_bp.route('/api/chatbot/enquiry-stats', methods=['GET'])
@jwt_required()
def get_enquiry_stats():
    """Get enquiry statistics"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service is not available'
            }), 503
        
        stats = gemini_chatbot_service.get_enquiry_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting enquiry stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chatbot_bp.route('/api/chatbot/client-stats', methods=['GET'])
@jwt_required()
def get_client_stats():
    """Get client statistics"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service is not available'
            }), 503
        
        stats = gemini_chatbot_service.get_client_stats()
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting client stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chatbot_bp.route('/api/chatbot/lookup/gst/<gst_number>', methods=['GET'])
@jwt_required()
def lookup_by_gst(gst_number):
    """Lookup client by GST number"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service is not available'
            }), 503
        
        client = gemini_chatbot_service.get_client_by_gst(gst_number)
        
        if client:
            return jsonify({
                'success': True,
                'data': client
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No client found with GST number: {gst_number}'
            }), 404
        
    except Exception as e:
        logger.error(f"Error looking up client by GST: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chatbot_bp.route('/api/chatbot/lookup/mobile/<mobile_number>', methods=['GET'])
@jwt_required()
def lookup_by_mobile(mobile_number):
    """Lookup client by mobile number"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'error': 'Chatbot service is not available'
            }), 503
        
        client = gemini_chatbot_service.get_client_by_mobile(mobile_number)
        
        if client:
            return jsonify({
                'success': True,
                'data': client
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No client found with mobile number: {mobile_number}'
            }), 404
        
    except Exception as e:
        logger.error(f"Error looking up client by mobile: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chatbot_bp.route('/api/chatbot/health', methods=['GET'])
def health_check():
    """Health check endpoint for chatbot service"""
    try:
        if not CHATBOT_SERVICE_AVAILABLE or not gemini_chatbot_service:
            return jsonify({
                'success': False,
                'status': 'Service unavailable',
                'error': 'Chatbot service is not available'
            }), 503
        
        # Test MongoDB connection
        gemini_chatbot_service.client.admin.command('ping')
        
        return jsonify({
            'success': True,
            'status': 'Healthy',
            'services': {
                'gemini_ai': True,
                'mongodb': True,
                'chatbot_service': True
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'Unhealthy',
            'error': str(e)
        }), 500

def analyze_query(message: str) -> Dict[str, Any]:
    """Analyze user query to determine type and extract parameters"""
    from datetime import datetime
    
    message_lower = message.lower()
    
    # GST number patterns
    gst_patterns = [
        r'gst\s*(?:number|no\.?|#)?\s*:?\s*([A-Z0-9]{15})',
        r'([A-Z0-9]{15})',  # Direct GST number
        r'gst\s+([A-Z0-9]{15})',
        r'([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1})'  # GST format
    ]
    
    # Mobile number patterns
    mobile_patterns = [
        r'mobile\s*(?:number|no\.?|#)?\s*:?\s*([6-9]\d{9})',
        r'phone\s*(?:number|no\.?|#)?\s*:?\s*([6-9]\d{9})',
        r'contact\s*(?:number|no\.?|#)?\s*:?\s*([6-9]\d{9})',
        r'([6-9]\d{9})'  # Direct mobile number
    ]
    
    # Check for GST lookup
    for pattern in gst_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            gst_number = match.group(1)
            if len(gst_number) == 15:  # Valid GST length
                return {
                    'type': 'specific_query',
                    'query_type': 'gst_lookup',
                    'parameters': {'gst_number': gst_number},
                    'timestamp': datetime.now().isoformat()
                }
    
    # Check for mobile lookup
    for pattern in mobile_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            mobile_number = match.group(1)
            if len(mobile_number) == 10:  # Valid mobile length
                return {
                    'type': 'specific_query',
                    'query_type': 'mobile_lookup',
                    'parameters': {'mobile_number': mobile_number},
                    'timestamp': datetime.now().isoformat()
                }
    
    # Determine context type for general queries
    context_type = None
    if any(word in message_lower for word in ['enquiry', 'enquiries', 'inquiry', 'inquiries', 'enq', 'enquiry details', 'enquiry page']):
        context_type = 'enquiry'
    elif any(word in message_lower for word in ['client', 'clients', 'customer', 'customers', 'client details', 'client page', 'gst', 'pan']):
        context_type = 'client'
    
    # Enhanced detection for full access requests
    if any(word in message_lower for word in ['analyze', 'details', 'information', 'data', 'access', 'full access']):
        if context_type is None:
            # If no specific context but asking for analysis, default to client context
            if 'enquiry' in message_lower or 'enq' in message_lower:
                context_type = 'enquiry'
            elif 'client' in message_lower or 'customer' in message_lower:
                context_type = 'client'
    
    return {
        'type': 'general_query',
        'context_type': context_type,
        'timestamp': datetime.now().isoformat()
    }

# Error handlers
@chatbot_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@chatbot_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed'
    }), 405

@chatbot_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
