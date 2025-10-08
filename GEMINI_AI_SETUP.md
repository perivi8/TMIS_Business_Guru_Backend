# 🤖 Gemini AI Integration Setup Guide

This guide explains how to set up and use the Gemini AI integration for automatic GST document data extraction in the TMIS Business Guru application.

## 📋 Prerequisites

1. **Google AI Studio Account**: You need a Google account to access Google AI Studio
2. **Gemini API Key**: Get your API key from Google AI Studio
3. **Python Dependencies**: Required libraries are listed in `requirements.txt`

## 🔑 Getting Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key
5. Keep it secure - don't share it publicly

## ⚙️ Backend Setup

### 1. Update Environment Variables

The Gemini API key is already configured in the backend `.env` file:

```bash
# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyC51gSO_1tZaXEfHZDUuU3Z0DuAkssiM3k
```

**⚠️ Important**: Replace the existing API key with your own valid Gemini API key.

### 2. Install Dependencies

Make sure all required Python packages are installed:

```bash
cd TMIS_Business_Guru_Backend
pip install -r requirements.txt
```

Key dependencies for AI functionality:
- `google-generativeai==0.3.2` - Gemini AI SDK
- `pytesseract==0.3.10` - OCR for image processing
- `Pillow==10.2.0` - Image processing

### 3. Install Tesseract OCR (for image processing)

**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install it (default location: `C:\Program Files\Tesseract-OCR\`)
3. Add to PATH or update code with custom path

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### 4. Test the Integration

Run the test script to verify everything is working:

```bash
python test_gemini_integration.py
```

Expected output:
```
🚀 TMIS Business Guru - Gemini AI Integration Test
==================================================
🔍 Testing Gemini AI Integration...
✅ GEMINI_API_KEY found: AIzaSyC51g...
✅ Gemini AI is working correctly!
📄 Sample response: {"registration_number": "27AABCU9603R1ZX"...

🔍 Testing DocumentProcessor class...
✅ DocumentProcessor initialized successfully
✅ DocumentProcessor is configured to use Gemini AI

==================================================
📊 Test Results:
   Gemini AI Connection: ✅ PASS
   DocumentProcessor:    ✅ PASS

🎉 All tests passed! The AI integration is ready to use.
```

## 🎯 How It Works

### 1. Document Upload
When a user uploads a GST document (PDF, JPG, PNG) in the new client form, the file is temporarily stored on the server.

### 2. AI Processing
The `DocumentProcessor` class:
1. **Extracts text** from the document (PDF text extraction or OCR for images)
2. **Sends to Gemini AI** with a structured prompt asking for specific GST information
3. **Parses the AI response** as JSON
4. **Falls back to regex** if AI processing fails

### 3. Data Population
Extracted data automatically fills the form fields:
- Registration Number (GSTIN)
- Legal Name
- Trade Name
- Address
- State
- District
- Pincode
- GST Status
- Business Type

### 4. User Experience
- Click the ⚡ AI icon next to any field
- See a loading spinner while processing
- Form fields auto-populate with extracted data
- Success/error messages provide feedback

## 🔧 API Endpoints

### Extract GST Data (Direct)
```
POST /api/clients/extract-gst-data
Content-Type: multipart/form-data
Authorization: Bearer <jwt_token>

Body:
- gst_document: File (PDF/JPG/PNG)
```

Response:
```json
{
  "success": true,
  "extracted_data": {
    "registration_number": "27AABCU9603R1ZX",
    "legal_name": "ABC PRIVATE LIMITED",
    "trade_name": "ABC Company",
    "address": "123 Business Street, Mumbai",
    "state": "Maharashtra",
    "district": "Mumbai",
    "pincode": "400001",
    "gst_status": "Active",
    "business_type": "Private Limited"
  }
}
```

## 🛠️ Troubleshooting

### Common Issues:

1. **"GEMINI_API_KEY not found"**
   - Check if the `.env` file exists in the backend directory
   - Verify the API key is correctly set
   - Restart the backend server after changes

2. **"Failed to initialize Gemini AI"**
   - Verify your API key is valid
   - Check internet connectivity
   - Ensure `google-generativeai` package is installed

3. **OCR not working for images**
   - Install Tesseract OCR system dependency
   - For Windows, add Tesseract to PATH
   - Verify `pytesseract` package is installed

4. **"Document processing service not available"**
   - Check if `DocumentProcessor` import is successful
   - Verify all dependencies are installed
   - Check server logs for detailed error messages

### Debug Mode:

Enable detailed logging by setting the log level in `document_processor.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Performance Notes

- **AI Processing**: Takes 2-5 seconds depending on document complexity
- **Fallback Mode**: Regex processing is instant but less accurate
- **File Size Limits**: Recommended max 10MB per document
- **Supported Formats**: PDF, JPG, JPEG, PNG, BMP, TIFF

## 🔒 Security Considerations

1. **API Key Security**: Never commit API keys to version control
2. **File Cleanup**: Temporary files are automatically deleted after processing
3. **Rate Limits**: Gemini API has usage quotas - monitor your usage
4. **Data Privacy**: Document content is sent to Google's servers for processing

## 🚀 Usage in Frontend

The AI functionality is already integrated in the new client form. Users can:

1. Upload a GST document
2. Click the ⚡ AI icon next to any field
3. Wait for processing (loading spinner shows)
4. Review and edit the auto-populated data

The frontend automatically calls the backend API and handles the response.

## 📈 Future Enhancements

Potential improvements:
- Support for more document types (PAN, Aadhar, Bank statements)
- Batch processing of multiple documents
- Confidence scores for extracted data
- Manual correction and learning capabilities
- Integration with other AI models for comparison

---

**Need Help?** Check the server logs or run the test script to diagnose issues.
