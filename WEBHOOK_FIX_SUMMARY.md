# WhatsApp Webhook Fix Summary

## Issues Fixed

### 1. ✅ WhatsApp Username Capture
**Problem**: The webhook was not properly capturing the WhatsApp username/display name from incoming messages.

**Solution**: Enhanced the `_extract_message_info()` function to:
- Try multiple fields for sender name: `senderName`, `chatName`, `pushName`, `notifyName`
- Use priority order to select the best available name
- Handle different GreenAPI webhook formats

### 2. ✅ Mobile Number Extraction
**Problem**: Mobile number extraction was basic and didn't handle all formats properly.

**Solution**: Improved mobile number processing:
- Clean and format mobile numbers by removing non-digit characters
- Extract from chat ID by removing `@c.us` suffix
- Ensure proper format for database storage

### 3. ✅ Database Storage Enhancement
**Problem**: Enquiry records were missing WhatsApp-specific fields and proper data structure.

**Solution**: Enhanced enquiry creation with:
- `user_name`: Actual WhatsApp username/display name
- `whatsapp_sender_name`: WhatsApp sender name
- `whatsapp_chat_id`: Original chat ID
- `whatsapp_message_text`: Original message text
- `source`: Set to 'whatsapp_webhook' for tracking
- Duplicate prevention using message ID

### 4. ✅ Improved Logging
**Problem**: Limited debugging information for webhook processing.

**Solution**: Added comprehensive logging:
- Detailed extraction process logging
- Sender data field inspection
- Enquiry creation confirmation
- Error handling with detailed messages

## Code Changes Made

### File: `enquiry_routes.py`

#### Enhanced `_extract_message_info()` function:
- Added support for multiple sender name fields
- Improved handling of different webhook formats
- Better error handling and logging

#### Enhanced `_create_enquiry_from_message()` function:
- Added proper WhatsApp username capture
- Improved mobile number cleaning
- Added WhatsApp-specific database fields
- Added duplicate prevention
- Enhanced socket event emission

## Database Schema Updates

The enquiry records now include these additional fields:
```json
{
  "user_name": "WhatsApp display name",
  "whatsapp_sender_name": "Sender name from WhatsApp",
  "whatsapp_chat_id": "Original chat ID (e.g., 918106811285@c.us)",
  "whatsapp_message_text": "Original message text",
  "whatsapp_message_id": "Unique message ID",
  "source": "whatsapp_webhook",
  "additional_comments": "Received via WhatsApp: \"message text\""
}
```

## Testing

### Webhook URL
The webhook is configured at: `https://tmis-business-guru-backend.onrender.com/api/enquiries/whatsapp/webhook`

### Test Data Format
GreenAPI sends data in this format:
```json
{
  "typeWebhook": "incomingMessageReceived",
  "messageData": {
    "textMessage": {
      "text": "Hi I am interested!"
    },
    "idMessage": "message_id_123"
  },
  "senderData": {
    "chatId": "918106811285@c.us",
    "senderName": "John Doe",
    "pushName": "John Doe WhatsApp",
    "chatName": "John Doe Chat"
  }
}
```

### Expected Result
When someone clicks the WhatsApp link and sends "Hi I am interested!", the system will now:

1. ✅ Capture their mobile number: `918106811285`
2. ✅ Capture their WhatsApp username: `John Doe` (or best available name)
3. ✅ Store complete enquiry record in MongoDB
4. ✅ Emit real-time notification to frontend
5. ✅ Prevent duplicate entries

## Environment Variables for Render

All required environment variables are already configured in your `.env` file:

### Database
- `MONGODB_URI`: ✅ Configured
- `JWT_SECRET_KEY`: ✅ Configured

### WhatsApp (GreenAPI)
- `GREENAPI_INSTANCE_ID`: ✅ Configured (7105335459)
- `GREENAPI_TOKEN`: ✅ Configured
- `GREENAPI_BASE_URL`: ✅ Configured

### Email
- `SMTP_EMAIL`: ✅ Configured
- `SMTP_PASSWORD`: ✅ Configured
- `SMTP_SERVER`: ✅ Configured
- `SMTP_PORT`: ✅ Configured

### Other
- `FLASK_ENV`: ✅ Set to production
- `CLOUDINARY_*`: ✅ Configured for file uploads

## Deployment Steps

1. **Deploy to Render**: The code changes are ready for deployment
2. **Verify Environment Variables**: All required variables are in `.env`
3. **Test Webhook**: Use the GreenAPI webhook URL in your settings
4. **Monitor Logs**: Check Render logs for webhook processing

## How to Test

1. Share the WhatsApp link: `https://wa.me/918106811285?text=Hi%20I%20am%20interested!`
2. When someone clicks and sends the message, check:
   - Render logs for webhook processing
   - MongoDB for new enquiry record
   - Frontend for real-time notification

## Troubleshooting

### If mobile number is not captured:
- Check Render logs for `chat_id` extraction
- Verify GreenAPI is sending `senderData.chatId`

### If username is not captured:
- Check logs for available sender name fields
- GreenAPI may not always provide all name fields

### If enquiry is not created:
- Check MongoDB connection in Render logs
- Verify webhook URL is correctly configured in GreenAPI

## Status: ✅ READY FOR DEPLOYMENT

All fixes have been implemented and the webhook should now properly capture both WhatsApp mobile numbers and usernames when someone sends an "interested" message through your WhatsApp link.
