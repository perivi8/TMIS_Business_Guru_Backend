# TMIS Business Guru Backend Deployment Guide

## Render Deployment Steps

### Option 1: Try with Updated Requirements (Recommended)
1. Use the updated `requirements.txt` with newer package versions
2. Ensure `runtime.txt` and `.python-version` files are present
3. Deploy using `render.yaml` configuration

### Option 2: Minimal Deployment (If Option 1 Fails)
1. Replace `requirements.txt` with `requirements-minimal.txt`
2. This removes potentially problematic packages:
   - PyPDF2 (PDF processing)
   - Pillow (Image processing)
   - pandas (Data analysis)
   - openpyxl (Excel processing)
   - cloudinary (Cloud storage)
   - email-validator (Email validation)

### Environment Variables to Set in Render Dashboard
```
JWT_SECRET_KEY=tmis-business-guru-secret-key-2024
MONGODB_URI=your_mongodb_atlas_connection_string
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
FLASK_ENV=production
```

### Files Created for Deployment
- `runtime.txt` - Specifies Python 3.11.9
- `.python-version` - Alternative Python version specification
- `render.yaml` - Complete Render configuration
- `Procfile` - Alternative deployment configuration
- `requirements-minimal.txt` - Minimal dependencies fallback
- `DEPLOYMENT.md` - This guide

### Health Check
Once deployed, test the health endpoint:
```
GET https://your-app-name.onrender.com/health
```

### Troubleshooting
1. If build fails, try using `requirements-minimal.txt`
2. Check Render logs for specific error messages
3. Ensure all environment variables are set
4. Verify Python version is 3.11.9 in build logs
