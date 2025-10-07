# TMIS Gemini AI Chatbot Feature

## Overview

The TMIS Business Guru system now includes an intelligent AI chatbot powered by Google's Gemini AI. This chatbot provides users with instant access to business data, client information, enquiry statistics, and more through natural language queries.

## Features

### 🤖 **AI-Powered Responses**
- Powered by Google Gemini AI for intelligent, contextual responses
- Natural language processing for user queries
- Smart context detection (enquiry vs client queries)

### 📊 **Data Access**
- **Enquiry Reports**: Get statistics, counts, and insights about enquiries
- **Client Information**: Search by GST number or mobile number
- **Document Status**: Check what documents clients have shared
- **Loan Status**: View loan application status and distribution
- **General Analytics**: Business insights and data summaries

### 🔍 **Smart Search Capabilities**
- **GST Lookup**: Enter any GST number to get complete client details
- **Mobile Search**: Find clients by mobile number
- **Status Checking**: Get loan status, document status, and more
- **Statistical Queries**: Ask about counts, distributions, and trends

## Usage Examples

### Basic Queries
```
"How many enquiries do we have?"
"Show me client statistics"
"What's the status distribution of our clients?"
```

### Specific Lookups
```
"GST: 22AAAAA0000A1Z5"
"Mobile: 9876543210"
"Find client with GST number 27ABCDE1234F1Z5"
```

### Advanced Questions
```
"How many enquiries were received in the last 30 days?"
"Show me clients with pending loan status"
"Which staff member has the most enquiries?"
```

## Technical Implementation

### Backend Components

#### 1. **Gemini Chatbot Service** (`gemini_chatbot_service.py`)
- Core service handling AI interactions
- MongoDB data access and processing
- Response generation and formatting

#### 2. **Chatbot Routes** (`chatbot_routes.py`)
- RESTful API endpoints for chatbot functionality
- Authentication and error handling
- Query analysis and routing

#### 3. **API Endpoints**
- `POST /api/chatbot/chat` - Main chat endpoint
- `GET /api/chatbot/enquiry-stats` - Enquiry statistics
- `GET /api/chatbot/client-stats` - Client statistics
- `GET /api/chatbot/lookup/gst/<gst_number>` - GST lookup
- `GET /api/chatbot/lookup/mobile/<mobile_number>` - Mobile lookup
- `GET /api/chatbot/health` - Health check

### Frontend Components

#### 1. **Chatbot Component** (`chatbot.component.ts`)
- Main chatbot interface
- Message handling and display
- Real-time communication with backend

#### 2. **Chatbot Service** (`chatbot.service.ts`)
- Angular service for API communication
- State management for chatbot visibility
- HTTP request handling

#### 3. **Integration**
- Integrated into navbar with Gemini AI icon
- Global availability across the application
- Responsive design for mobile and desktop

## Configuration

### Environment Variables
```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB Configuration (existing)
MONGODB_URI=your_mongodb_connection_string
```

### Dependencies
```txt
# Backend
google-generativeai==0.3.2

# Frontend (already included)
@angular/material
@angular/common/http
```

## Installation & Setup

### 1. Backend Setup
```bash
# Install Python dependencies
pip install google-generativeai==0.3.2

# Set environment variables in .env file
GEMINI_API_KEY=your_api_key_here

# Test the setup
python test_chatbot.py
```

### 2. Frontend Setup
```bash
# Install Angular dependencies (if not already installed)
npm install

# Build and serve
ng serve
```

### 3. API Key Setup
1. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file as `GEMINI_API_KEY`
3. Restart your backend server

## Security Features

- **JWT Authentication**: All chatbot endpoints require valid JWT tokens
- **API Key Protection**: Gemini API key is stored securely in environment variables
- **Input Validation**: All user inputs are validated and sanitized
- **Error Handling**: Comprehensive error handling with user-friendly messages

## Data Privacy

- **No Data Storage**: Chat conversations are not stored permanently
- **Secure Transmission**: All data is transmitted over HTTPS
- **Access Control**: Only authenticated users can access the chatbot
- **Data Filtering**: Only relevant business data is shared with the AI

## Troubleshooting

### Common Issues

#### 1. **Chatbot Not Responding**
- Check if Gemini API key is set correctly
- Verify internet connection
- Check backend server logs

#### 2. **"Service Unavailable" Error**
- Ensure MongoDB is connected
- Check if all required Python packages are installed
- Verify environment variables are loaded

#### 3. **Authentication Errors**
- Ensure user is logged in
- Check if JWT token is valid
- Verify API endpoints are accessible

### Testing
```bash
# Test backend functionality
python test_chatbot.py

# Check API health
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5000/api/chatbot/health
```

## Future Enhancements

### Planned Features
- **Voice Input**: Speech-to-text integration
- **File Analysis**: Upload and analyze documents
- **Advanced Analytics**: Predictive insights and trends
- **Multi-language Support**: Support for regional languages
- **Custom Training**: Domain-specific AI training

### Integration Possibilities
- **WhatsApp Integration**: Chatbot via WhatsApp
- **Email Automation**: AI-powered email responses
- **Report Generation**: Automated report creation
- **Workflow Automation**: AI-driven business processes

## Support

For technical support or feature requests:
1. Check the troubleshooting section above
2. Review backend logs in the console
3. Test with the provided test script
4. Contact the development team

## API Reference

### Chat Endpoint
```http
POST /api/chatbot/chat
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "message": "How many enquiries do we have?"
}
```

**Response:**
```json
{
  "success": true,
  "response": "Based on your data, you currently have 150 enquiries in your system...",
  "query_type": "general",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Health Check
```http
GET /api/chatbot/health

Response:
{
  "success": true,
  "status": "Healthy",
  "services": {
    "gemini_ai": true,
    "mongodb": true,
    "chatbot_service": true
  }
}
```

---

**Built with ❤️ for TMIS Business Guru**
