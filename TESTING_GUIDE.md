# WhatsApp Webhook Testing Guide

## 🚀 Quick Test After Deployment

### 1. Test Webhook Status
```bash
curl https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook/test
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Enhanced webhook handler is running with username capture fix",
  "version": "2.1",
  "features": [
    "WhatsApp username capture",
    "Enhanced mobile number extraction",
    "Duplicate prevention",
    "Comprehensive logging",
    "Multiple sender name field support"
  ]
}
```

### 2. Test Data Processing
```bash
curl -X POST https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook/test-data \
  -H "Content-Type: application/json" \
  -d '{
    "typeWebhook": "incomingMessageReceived",
    "messageData": {
      "textMessage": {
        "text": "Hi I am interested!"
      },
      "idMessage": "test_123"
    },
    "senderData": {
      "chatId": "918106811285@c.us",
      "senderName": "John Doe",
      "pushName": "John WhatsApp Name"
    }
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Webhook data processing test completed",
  "extracted_info": {
    "has_message_data": true,
    "chat_id": "918106811285@c.us",
    "message_text": "Hi I am interested!",
    "sender_name": "John Doe",
    "message_id": "test_123"
  },
  "processed_data": {
    "display_name": "John Doe",
    "whatsapp_username": "John Doe",
    "mobile_number": "918106811285",
    "original_chat_id": "918106811285@c.us",
    "message_text": "Hi I am interested!"
  },
  "would_create_enquiry": true
}
```

## 🔧 Render Environment Variables

Make sure these are set in your Render dashboard:

### Required Variables
```
MONGODB_URI=mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0
JWT_SECRET_KEY=tmis-business-guru-secret-key-2024
FLASK_ENV=production
GREENAPI_INSTANCE_ID=7105335459
GREENAPI_TOKEN=3a0876a6822049bc8764168532cb912b16ba62dcb2f446eb99
GREENAPI_BASE_URL=https://api.green-api.com
SMTP_EMAIL=perivihk@gmail.com
SMTP_PASSWORD=pbjmpvmstqzrmkbb
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
CLOUDINARY_API_KEY=685119388195111
CLOUDINARY_API_SECRET=WxzTmdK9bzyXrutVrrhw-AkLeps
CLOUDINARY_CLOUD_NAME=dnwplyizd
CLOUDINARY_ENABLED=true
GEMINI_API_KEY=AIzaSyC51gSO_1tZaXEfHZDUuU3Z0DuAkssiM3k
```

## 📱 Real WhatsApp Testing

### 1. Configure GreenAPI Webhook
In your GreenAPI dashboard, set the webhook URL to:
```
https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook
```

### 2. Test the WhatsApp Link
Share this link with someone:
```
https://wa.me/918106811285?text=Hi%20I%20am%20interested!
```

### 3. What Should Happen
1. Person clicks the link
2. WhatsApp opens with pre-filled message "Hi I am interested!"
3. Person sends the message
4. GreenAPI sends webhook to your backend
5. Backend processes the message and creates enquiry
6. You should see in Render logs:
   ```
   📥 === NEW WEBHOOK REQUEST ===
   📋 Creating enquiry from WhatsApp message:
      Original Chat ID: 918106811285@c.us
      Clean Number: 918106811285
      Sender Name: [Their WhatsApp Name]
   ✅ New WhatsApp enquiry created successfully
   ```

## 🔍 Troubleshooting

### Issue: No mobile number captured
**Check**: Render logs for `chat_id` extraction
**Solution**: Verify GreenAPI webhook format

### Issue: No username captured
**Check**: Render logs for available sender name fields
**Note**: GreenAPI may not always provide all name fields

### Issue: Enquiry not created
**Check**: 
1. MongoDB connection in logs
2. Webhook URL in GreenAPI settings
3. Message contains "interested" keyword

### Issue: Duplicate enquiries
**Note**: System now prevents duplicates using message ID

## 📊 Monitoring

### Check Render Logs
Look for these log patterns:
- `📥 === NEW WEBHOOK REQUEST ===`
- `📋 Creating enquiry from WhatsApp message:`
- `✅ New WhatsApp enquiry created successfully`

### Check MongoDB
Query for recent enquiries:
```javascript
db.enquiries.find({
  "source": "whatsapp_webhook"
}).sort({"created_at": -1}).limit(10)
```

### Check Frontend
- Real-time notifications should appear
- Enquiry should show in the enquiries list
- WhatsApp-specific fields should be populated

## ✅ Success Indicators

1. **Webhook Status**: Test endpoint returns version 2.1
2. **Data Processing**: Test data endpoint processes correctly
3. **Real Message**: Actual WhatsApp message creates enquiry
4. **Database**: Enquiry stored with WhatsApp fields
5. **Frontend**: Real-time notification received

## 🎉 Expected Results

After someone sends "Hi I am interested!" via your WhatsApp link:

### Database Record
```json
{
  "_id": "...",
  "wati_name": "John Doe",
  "user_name": "John Doe",
  "mobile_number": "918106811285",
  "whatsapp_sender_name": "John Doe",
  "whatsapp_chat_id": "918106811285@c.us",
  "whatsapp_message_text": "Hi I am interested!",
  "comments": "New Enquiry - Interested",
  "additional_comments": "Received via WhatsApp: \"Hi I am interested!\"",
  "staff": "WhatsApp Bot",
  "source": "whatsapp_webhook",
  "created_at": "2025-10-09T10:30:00.000Z"
}
```

### Frontend Display
- **Name**: John Doe (WhatsApp username)
- **Mobile**: 918106811285 (extracted from chat ID)
- **Source**: WhatsApp Webhook
- **Comments**: New Enquiry - Interested

## 🔄 Deployment Checklist

- [ ] Code changes deployed to Render
- [ ] Environment variables configured
- [ ] GreenAPI webhook URL updated
- [ ] Test endpoints working
- [ ] Real WhatsApp test successful
- [ ] Database records created correctly
- [ ] Frontend notifications working

---

**Status**: ✅ Ready for testing after deployment
