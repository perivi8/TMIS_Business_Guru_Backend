import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiChatbotService:
    def __init__(self):
        """Initialize Gemini AI chatbot service"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.mongodb_uri = os.getenv('MONGODB_URI')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        if not self.mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment variables")
        
        # Configure Gemini AI
        genai.configure(api_key=self.api_key)
        # Use gemini-flash-latest as it's more reliable and supported
        self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # Initialize MongoDB connection
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client.tmis_business_guru
            
            # Collections
            self.clients_collection = self.db.clients
            self.enquiries_collection = self.db.enquiries
            self.users_collection = self.db.users
            
            logger.info("✅ Gemini Chatbot Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def serialize_document(self, doc: Dict) -> Dict:
        """Convert MongoDB document to JSON serializable format"""
        if doc:
            if '_id' in doc and isinstance(doc['_id'], ObjectId):
                doc['_id'] = str(doc['_id'])
            
            # Convert datetime objects to ISO format
            for key, value in doc.items():
                if isinstance(value, datetime):
                    doc[key] = value.isoformat()
                elif isinstance(value, ObjectId):
                    doc[key] = str(value)
        
        return doc
    
    def get_enquiry_data(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch enquiry data from MongoDB"""
        try:
            query = {}
            if filters:
                # Add filters like date range, staff, status etc.
                if 'date_from' in filters:
                    query['date'] = {'$gte': datetime.fromisoformat(filters['date_from'])}
                if 'date_to' in filters:
                    if 'date' not in query:
                        query['date'] = {}
                    query['date']['$lte'] = datetime.fromisoformat(filters['date_to'])
                if 'staff' in filters:
                    query['staff'] = {'$regex': filters['staff'], '$options': 'i'}
                if 'mobile_number' in filters:
                    query['mobile_number'] = filters['mobile_number']
            
            enquiries = list(self.enquiries_collection.find(query).sort('date', -1).limit(100))
            return [self.serialize_document(enq) for enq in enquiries]
            
        except Exception as e:
            logger.error(f"Error fetching enquiry data: {e}")
            return []
    
    def get_client_data(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Fetch client data from MongoDB"""
        try:
            query = {}
            if filters:
                if 'gst_number' in filters:
                    query['business_pan'] = {'$regex': filters['gst_number'], '$options': 'i'}
                if 'mobile_number' in filters:
                    query['mobile_number'] = filters['mobile_number']
                if 'status' in filters:
                    query['status'] = filters['status']
                if 'loan_status' in filters:
                    query['loan_status'] = filters['loan_status']
            
            clients = list(self.clients_collection.find(query).sort('created_at', -1).limit(100))
            return [self.serialize_document(client) for client in clients]
            
        except Exception as e:
            logger.error(f"Error fetching client data: {e}")
            return []
    
    def get_client_by_gst(self, gst_number: str) -> Optional[Dict]:
        """Get client by GST number"""
        try:
            client = self.clients_collection.find_one({
                '$or': [
                    {'business_pan': {'$regex': gst_number, '$options': 'i'}},
                    {'gst_number': {'$regex': gst_number, '$options': 'i'}}
                ]
            })
            
            if client:
                return self.serialize_document(client)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching client by GST: {e}")
            return None
    
    def get_client_by_mobile(self, mobile_number: str) -> Optional[Dict]:
        """Get client by mobile number"""
        try:
            client = self.clients_collection.find_one({
                'mobile_number': mobile_number
            })
            
            if client:
                return self.serialize_document(client)
            return None
            
        except Exception as e:
            logger.error(f"Error fetching client by mobile: {e}")
            return None
    
    def get_enquiry_stats(self) -> Dict:
        """Get enquiry statistics"""
        try:
            total_enquiries = self.enquiries_collection.count_documents({})
            
            # Get enquiries by date (last 30 days)
            from datetime import timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_enquiries = self.enquiries_collection.count_documents({
                'date': {'$gte': thirty_days_ago}
            })
            
            # Get enquiries by staff
            staff_pipeline = [
                {'$group': {'_id': '$staff', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            staff_stats = list(self.enquiries_collection.aggregate(staff_pipeline))
            
            return {
                'total_enquiries': total_enquiries,
                'recent_enquiries': recent_enquiries,
                'staff_stats': staff_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting enquiry stats: {e}")
            return {}
    
    def get_client_stats(self) -> Dict:
        """Get client statistics"""
        try:
            total_clients = self.clients_collection.count_documents({})
            
            # Get clients by status
            status_pipeline = [
                {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            status_stats = list(self.clients_collection.aggregate(status_pipeline))
            
            # Get clients by loan status
            loan_status_pipeline = [
                {'$group': {'_id': '$loan_status', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            loan_stats = list(self.clients_collection.aggregate(loan_status_pipeline))
            
            # Get GST status distribution
            gst_pipeline = [
                {'$group': {'_id': '$gst_status', 'count': {'$sum': 1}}},
                {'$sort': {'count': -1}}
            ]
            gst_stats = list(self.clients_collection.aggregate(gst_pipeline))
            
            return {
                'total_clients': total_clients,
                'status_stats': status_stats,
                'loan_stats': loan_stats,
                'gst_stats': gst_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting client stats: {e}")
            return {}
    
    def generate_response(self, user_query: str, context_type: Optional[str] = None) -> str:
        """Generate AI response using Gemini"""
        try:
            # Prepare context based on query type
            context_data = ""
            
            # Determine if user is asking about enquiries or clients
            is_enquiry_query = any(word in user_query.lower() for word in ['enquiry', 'enquiries', 'inquiry', 'inquiries'])
            is_client_query = any(word in user_query.lower() for word in ['client', 'clients', 'customer', 'customers', 'gst', 'pan'])
            
            # Get relevant data based on context
            if is_enquiry_query or context_type == "enquiry":
                enquiry_stats = self.get_enquiry_stats()
                recent_enquiries = self.get_enquiry_data()[:10]  # Get last 10 enquiries for more detail
                
                context_data = f"""
                ENQUIRY DATA CONTEXT:
                - Total Enquiries: {enquiry_stats.get('total_enquiries', 0)}
                - Recent Enquiries (30 days): {enquiry_stats.get('recent_enquiries', 0)}
                - Staff Performance: {json.dumps(enquiry_stats.get('staff_stats', []), indent=2)}
                
                Recent Enquiries Sample (Last 10):
                {json.dumps(recent_enquiries, indent=2, default=str)}
                """
                
            elif is_client_query or context_type == "client":
                client_stats = self.get_client_stats()
                recent_clients = self.get_client_data()[:10]  # Get last 10 clients for more detail
                
                context_data = f"""
                CLIENT DATA CONTEXT:
                - Total Clients: {client_stats.get('total_clients', 0)}
                - Status Distribution: {json.dumps(client_stats.get('status_stats', []), indent=2)}
                - Loan Status Distribution: {json.dumps(client_stats.get('loan_stats', []), indent=2)}
                - GST Status Distribution: {json.dumps(client_stats.get('gst_stats', []), indent=2)}
                
                Recent Clients Sample (Last 10):
                {json.dumps(recent_clients, indent=2, default=str)}
                """
            
            # Create comprehensive prompt
            prompt = f"""
            You are an AI assistant for TMIS Business Guru, a business management system. 
            You have access to detailed enquiry and client data from the system.
            
            SYSTEM ACCESS INSTRUCTIONS:
            - When asked about client details, you have FULL ACCESS to client information
            - When asked about enquiry details, you have FULL ACCESS to enquiry information
            - You can analyze any data related to clients or enquiries
            - You should provide comprehensive answers when asked about specific data
            
            {context_data}
            
            User Query: {user_query}
            
            Instructions:
            1. Provide accurate, detailed responses based on the data provided
            2. If asked about specific numbers or statistics, use the exact data from the context
            3. If asked about GST status or client details, provide comprehensive information
            4. If asked about enquiries, provide detailed insights from the enquiry data
            5. Be conversational but professional
            6. If you don't have specific data to answer a question, say so clearly
            7. Format your response in a clear, readable manner
            8. Use bullet points or numbered lists when appropriate
            9. When asked for analysis, provide detailed insights
            10. When asked for specific client or enquiry information, provide all relevant details
            
            Respond to the user's query now with full access to the requested information:
            """
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists. Error: {str(e)}"
    
    def process_specific_query(self, query_type: str, parameters: Dict) -> str:
        """Process specific queries like GST lookup, mobile search etc."""
        try:
            if query_type == "gst_lookup":
                gst_number = parameters.get('gst_number')
                if not gst_number:
                    return "Please provide a GST number to search for."
                
                client = self.get_client_by_gst(gst_number)
                if client:
                    return f"""
                    **Client Found for GST: {gst_number}**
                    
                    📋 **Basic Information:**
                    • Name: {client.get('user_name', 'N/A')}
                    • Business: {client.get('business_name', 'N/A')}
                    • Mobile: {client.get('mobile_number', 'N/A')}
                    • Email: {client.get('email', 'N/A')}
                    
                    📊 **Status Information:**
                    • Client Status: {client.get('status', 'N/A')}
                    • GST Status: {client.get('gst_status', 'N/A')}
                    • Loan Status: {client.get('loan_status', 'N/A')}
                    
                    💰 **Financial Details:**
                    • Required Loan Amount: ₹{client.get('required_loan_amount', 'N/A')}
                    • Bank Type: {client.get('bank_type', 'N/A')}
                    
                    📄 **Documents Status:**
                    {self._format_documents_status(client.get('documents', {}))}
                    """
                else:
                    return f"No client found with GST number: {gst_number}"
            
            elif query_type == "mobile_lookup":
                mobile_number = parameters.get('mobile_number')
                if not mobile_number:
                    return "Please provide a mobile number to search for."
                
                client = self.get_client_by_mobile(mobile_number)
                if client:
                    return f"""
                    **Client Found for Mobile: {mobile_number}**
                    
                    📋 **Basic Information:**
                    • Name: {client.get('user_name', 'N/A')}
                    • Business: {client.get('business_name', 'N/A')}
                    • GST/PAN: {client.get('business_pan', 'N/A')}
                    • Email: {client.get('email', 'N/A')}
                    
                    📊 **Status Information:**
                    • Client Status: {client.get('status', 'N/A')}
                    • GST Status: {client.get('gst_status', 'N/A')}
                    • Loan Status: {client.get('loan_status', 'N/A')}
                    
                    📄 **Documents Shared:**
                    {self._format_documents_status(client.get('documents', {}))}
                    """
                else:
                    return f"No client found with mobile number: {mobile_number}"
            
            else:
                return "Unknown query type. Please specify 'gst_lookup' or 'mobile_lookup'."
                
        except Exception as e:
            logger.error(f"Error processing specific query: {e}")
            return f"Error processing your request: {str(e)}"
    
    def _format_documents_status(self, documents: Dict) -> str:
        """Format documents status for display"""
        if not documents:
            return "• No documents uploaded yet"
        
        doc_status = []
        for doc_type, doc_info in documents.items():
            if isinstance(doc_info, dict):
                status = "✅ Uploaded" if doc_info.get('url') else "❌ Missing"
                doc_status.append(f"• {doc_type.replace('_', ' ').title()}: {status}")
            else:
                doc_status.append(f"• {doc_type.replace('_', ' ').title()}: ✅ Uploaded")
        
        return "\n".join(doc_status) if doc_status else "• No documents uploaded yet"

# Create global instance
try:
    gemini_chatbot_service = GeminiChatbotService()
    logger.info("✅ Gemini Chatbot Service instance created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create Gemini Chatbot Service: {e}")
    gemini_chatbot_service = None
