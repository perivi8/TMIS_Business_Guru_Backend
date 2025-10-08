# Chatbot Troubleshooting Guide

## Common Issues and Solutions

### 1. "Failed to load resource: net::ERR_FAILED"

This error typically occurs when:

#### **Backend Server Not Running**
```bash
# Start the backend server
cd TMIS_Business_Guru_Backend
python app.py
# or
python main.py
```

#### **Missing Dependencies**
```bash
# Install required packages
pip install google-generativeai==0.3.2
```

#### **Environment Variables Missing**
Check your `.env` file has:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

### 2. "Chatbot service is not available"

#### **Test the Service**
```bash
cd TMIS_Business_Guru_Backend
python test_chatbot.py
```

#### **Check API Health**
Open browser and go to:
```
http://localhost:5000/api/chatbot/health
```

### 3. Authentication Errors

#### **Check JWT Token**
- Make sure you're logged in
- Check browser console for token errors
- Try logging out and back in

### 4. Import Errors in Backend

#### **Check Python Environment**
```bash
# Check if packages are installed
pip list | grep google-generativeai
pip list | grep pymongo
pip list | grep flask
```

#### **Install Missing Packages**
```bash
pip install -r requirements.txt
```

### 5. Frontend Console Errors

#### **Check Browser Console**
1. Open Developer Tools (F12)
2. Check Console tab for errors
3. Look for network errors in Network tab

#### **Common Frontend Fixes**
```bash
# Rebuild Angular app
cd TMIS_Business_Guru
npm install
ng serve
```

### 6. API Endpoint Issues

#### **Verify Endpoints**
The following endpoints should be available:
- `POST /api/chatbot/chat`
- `GET /api/chatbot/health`
- `GET /api/chatbot/enquiry-stats`
- `GET /api/chatbot/client-stats`

#### **Test with cURL**
```bash
# Test health endpoint
curl http://localhost:5000/api/chatbot/health

# Test chat endpoint (requires auth)
curl -X POST http://localhost:5000/api/chatbot/chat \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## Quick Fixes

### 1. Restart Everything
```bash
# Stop all servers
# Then restart backend
cd TMIS_Business_Guru_Backend
python app.py

# In another terminal, restart frontend
cd TMIS_Business_Guru
ng serve
```

### 2. Clear Browser Cache
- Hard refresh: Ctrl+Shift+R
- Clear browser cache and cookies
- Try incognito/private mode

### 3. Check Network
- Ensure no firewall blocking localhost:5000
- Check if port 5000 is available
- Try different port if needed

## Debugging Steps

1. **Check Backend Logs**
   - Look at terminal running `python app.py`
   - Check for import errors or startup issues

2. **Check Frontend Console**
   - Open browser DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed requests

3. **Test Components Individually**
   ```bash
   # Test backend only
   python test_chatbot.py
   
   # Test API health
   curl http://localhost:5000/api/chatbot/health
   ```

4. **Verify Configuration**
   - Check environment.ts has correct API URL
   - Verify .env file has all required variables
   - Ensure MongoDB is accessible

## Still Having Issues?

If none of the above solutions work:

1. **Check the exact error message** in browser console
2. **Look at backend terminal** for Python errors
3. **Verify all files were created** as per the implementation
4. **Check if all imports are working** in both frontend and backend

## Contact Information

For additional support, provide:
- Exact error message
- Browser console logs
- Backend terminal output
- Steps to reproduce the issue
