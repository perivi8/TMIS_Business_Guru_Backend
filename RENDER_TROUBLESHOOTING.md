# Render Deployment Troubleshooting Guide

## 🚨 500 Internal Server Error - Debugging Steps

### Step 1: Check Render Logs
1. Go to your Render dashboard
2. Click on your backend service
3. Go to "Logs" tab
4. Look for error messages during startup

### Step 2: Test Health Endpoints
Once deployed, test these endpoints:

```bash
# Basic health check
curl https://tmis-business-guru-backend.onrender.com/health

# Debug environment variables
curl https://tmis-business-guru-backend.onrender.com/debug/env

# Test MongoDB connection
curl https://tmis-business-guru-backend.onrender.com/api/debug/database
```

### Step 3: Verify Environment Variables
In Render Dashboard, check these are set:

**Required Variables:**
- `MONGODB_URI` - Your complete MongoDB Atlas connection string
- `JWT_SECRET_KEY` - Should be `tmis-business-guru-secret-key-2024`
- `EMAIL_USER` - Your Gmail address
- `EMAIL_PASSWORD` - Your Gmail app password
- `SMTP_EMAIL` - Your Gmail address
- `SMTP_PASSWORD` - Your Gmail app password

**Optional but Recommended:**
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### Step 4: Common Issues and Solutions

#### Issue: MongoDB Connection Failed
**Symptoms:** Logs show "MongoDB connection failed"
**Solutions:**
1. Verify `MONGODB_URI` includes database name: `/tmis_business_guru`
2. Check MongoDB Atlas allows connections from `0.0.0.0/0`
3. Verify username/password in connection string

#### Issue: JWT Secret Key Error
**Symptoms:** "JWT_SECRET_KEY not properly configured"
**Solution:** Set `JWT_SECRET_KEY=tmis-business-guru-secret-key-2024`

#### Issue: Import Errors
**Symptoms:** "Failed to import modules"
**Solutions:**
1. Check all packages in `requirements.txt` are compatible
2. Try using `requirements-minimal.txt` instead
3. Check Python version is 3.11.9

#### Issue: Email Service Errors
**Symptoms:** Email-related errors in logs
**Solutions:**
1. Verify Gmail app password (not regular password)
2. Enable 2-factor authentication on Gmail
3. Generate new app password if needed

### Step 5: Manual Testing Script

Run this locally to test your configuration:

```bash
# Test MongoDB connection
python test_mongodb.py

# Test startup validation
python startup_check.py

# Test local server
python main.py
```

### Step 6: Deployment Checklist

Before deploying, ensure:
- [ ] `.env` file has correct MongoDB URI with database name
- [ ] JWT secret key is updated
- [ ] All environment variables are set in Render
- [ ] MongoDB Atlas allows connections from anywhere
- [ ] Gmail app password is generated and working
- [ ] `startup_check.py` passes all tests locally

### Step 7: Emergency Fallback

If all else fails, try minimal deployment:

1. Replace `requirements.txt` with `requirements-minimal.txt`
2. Comment out email service imports in `main.py`
3. Deploy with minimal functionality first
4. Add features back gradually

### Step 8: Get Help

If issues persist:
1. Check Render logs for specific error messages
2. Test health endpoints to isolate the problem
3. Run startup validation script locally
4. Verify all environment variables are correctly set

### Useful Commands

```bash
# Check if service is running
curl -I https://tmis-business-guru-backend.onrender.com/health

# Test specific endpoints
curl https://tmis-business-guru-backend.onrender.com/api/debug/database

# Check environment variables (remove in production)
curl https://tmis-business-guru-backend.onrender.com/debug/env
```

## 🔧 Quick Fixes

### Fix 1: MongoDB Connection String
```
# Wrong
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true

# Correct
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/tmis_business_guru?retryWrites=true
```

### Fix 2: Environment Variables in Render
Make sure these are set in Render Dashboard > Environment:
```
JWT_SECRET_KEY=tmis-business-guru-secret-key-2024
MONGODB_URI=your_complete_connection_string_with_database_name
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

### Fix 3: CORS Issues
If frontend can't connect, check `app.py` CORS configuration includes:
```python
CORS(app, origins=[
    "http://localhost:4200", 
    "http://localhost:4201", 
    "https://tmis-business-guru.vercel.app"
], supports_credentials=True)
```
