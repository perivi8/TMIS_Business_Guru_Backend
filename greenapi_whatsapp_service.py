#!/usr/bin/env python3
"""
GreenAPI WhatsApp Service - Send messages without OTP verification
Uses GreenAPI.com service which connects to regular WhatsApp
Enhanced with template support for TMIS enquiry system
"""

import requests
import json
import os
import logging
from dotenv import load_dotenv
from typing import Dict, Optional, Any

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GreenAPIWhatsAppService:
    """WhatsApp service using GreenAPI - NO OTP REQUIRED"""
    
    def __init__(self):
        self.instance_id = os.getenv('GREENAPI_INSTANCE_ID')
        self.token = os.getenv('GREENAPI_TOKEN')
        
        logger.info(f"🔧 GreenAPI Initialization:")
        logger.info(f"   Instance ID: {self.instance_id}")
        logger.info(f"   Token: {'Present' if self.token else 'Missing'}")
        
        if self.instance_id and self.token:
            # Use the correct GreenAPI endpoint format
            self.base_url = "https://api.green-api.com"
            self.api_available = True
            logger.info(f"✅ GreenAPI WhatsApp Service initialized - NO OTP REQUIRED")
            logger.info(f"   Instance ID: {self.instance_id}")
            logger.info(f"   Base URL: {self.base_url}")
        else:
            self.api_available = False
            logger.error("❌ GreenAPI credentials not found in .env file")
            logger.error(f"   Missing: GREENAPI_INSTANCE_ID={bool(self.instance_id)}, GREENAPI_TOKEN={bool(self.token)}")
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message via GreenAPI (no OTP required)
        
        Args:
            phone_number (str): Phone number with country code
            message (str): Message text
            
        Returns:
            Dict: Response from GreenAPI
        """
        if not self.api_available:
            return {
                'success': False,
                'error': 'GreenAPI credentials not configured',
                'solution': 'Add GREENAPI_INSTANCE_ID and GREENAPI_TOKEN to .env file'
            }
        
        try:
            # Format phone number for GreenAPI
            formatted_number = self._format_phone_number(phone_number)
            
            logger.info(f"🚀 GreenAPI - Sending to {formatted_number} (NO OTP REQUIRED)")
            logger.info(f"📱 Original phone number: {phone_number}")
            logger.info(f"📞 Formatted phone number: {formatted_number}")
            
            # Construct URL with proper formatting
            url = f"{self.base_url}/waInstance{self.instance_id}/sendMessage/{self.token}"
            logger.info(f"📤 Send URL: {url}")
            
            # Prepare data with proper structure
            data = {
                "chatId": formatted_number,
                "message": message
            }
            
            logger.info(f"📤 GreenAPI Payload: {json.dumps(data, indent=2, ensure_ascii=False)}")
            logger.info(f"📡 URL: {url}")
            
            # Add headers for proper API communication
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            logger.info(f"📤 Headers: {headers}")
            
            # Send request with timeout and headers
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response_data = response.json() if response.content else {}
            
            logger.info(f"📥 GreenAPI Response Status Code: {response.status_code}")
            logger.info(f"📥 GreenAPI Response Headers: {dict(response.headers)}")
            logger.info(f"📥 GreenAPI Response Content: {response.text}")
            logger.info(f"📥 GreenAPI Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False) if response_data else 'No response data'}")
            
            if response.status_code == 200 and response_data.get('idMessage'):
                logger.info(f"✅ GreenAPI SUCCESS! Message sent to {formatted_number}")
                return {
                    'success': True,
                    'message_id': response_data.get('idMessage'),
                    'service': 'GreenAPI',
                    'no_otp_required': True,
                    'response': response_data
                }
            else:
                # Handle different error cases
                if response.status_code == 400:
                    error_msg = response_data.get('message', 'Bad Request - Check phone number format or validity')
                elif response.status_code == 401:
                    error_msg = response_data.get('message', 'Unauthorized - Check API credentials')
                elif response.status_code == 403:
                    error_msg = response_data.get('message', 'Forbidden - Check API permissions')
                elif response.status_code == 404:
                    error_msg = response_data.get('message', 'Not Found - Check API endpoint')
                elif response.status_code == 466:
                    # Special handling for GreenAPI quota exceeded error
                    error_msg = response_data.get('invokeStatus', {}).get('description', 'Monthly quota exceeded')
                    if not error_msg or error_msg == 'Monthly quota exceeded':
                        error_msg = 'Monthly quota has been exceeded. Upgrade your GreenAPI plan to send to more numbers'
                else:
                    error_msg = response_data.get('message', f'Unknown GreenAPI error (Status: {response.status_code})')
                
                logger.error(f"❌ GreenAPI FAILED: {error_msg}")
                logger.error(f"❌ Status Code: {response.status_code}")
                logger.error(f"❌ Response Data: {json.dumps(response_data, indent=2, ensure_ascii=False) if response_data else 'No response data'}")
                
                # Provide more detailed error information
                detailed_error = f'GreenAPI error: {error_msg}'
                if response.status_code == 400:
                    detailed_error += ' (Bad Request - Check phone number format, validity, or if the number has WhatsApp)'
                elif response.status_code == 401:
                    detailed_error += ' (Unauthorized - Check API credentials)'
                elif response.status_code == 403:
                    detailed_error += ' (Forbidden - Check API permissions)'
                elif response.status_code == 404:
                    detailed_error += ' (Not Found - Check API endpoint)'
                elif response.status_code == 466:
                    detailed_error += ' (Monthly quota exceeded - Upgrade your GreenAPI plan to send to more numbers. Test number 8106811285 still works)'
                
                result = {
                    'success': False,
                    'error': detailed_error,
                    'service': 'GreenAPI',
                    'status_code': response.status_code,
                    'response': response_data,
                    'original_phone_number': phone_number,
                    'formatted_phone_number': formatted_number
                }
                
                # Add quota-specific information for 466 errors
                if response.status_code == 466:
                    result['quota_exceeded'] = True
                    result['working_test_number'] = '8106811285'
                    result['upgrade_url'] = 'https://console.green-api.com'
                    result['solution'] = 'Upgrade GreenAPI plan or use test number 8106811285'
                
                return result
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ GreenAPI Network error: {str(e)}")
            return {
                'success': False,
                'error': f'GreenAPI network error: {str(e)}',
                'service': 'GreenAPI',
                'original_phone_number': phone_number
            }
        except Exception as e:
            logger.error(f"❌ GreenAPI Unexpected error: {str(e)}")
            import traceback
            logger.error(f"❌ Error traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'GreenAPI unexpected error: {str(e)}',
                'service': 'GreenAPI',
                'original_phone_number': phone_number
            }
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for GreenAPI"""
        # Handle None or empty phone number
        if not phone_number:
            logger.warning("📱 _format_phone_number - Empty phone number provided")
            return ""
        
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, str(phone_number)))
        
        logger.info(f"📱 _format_phone_number - Input: {phone_number}, Cleaned: {clean_number}, Length: {len(clean_number)}")
        
        # Handle different cases based on number length
        if len(clean_number) == 0:
            logger.warning(f"   ⚠️ Invalid phone number format (empty): {phone_number}")
            return ""
        elif len(clean_number) < 10:
            # Too short - might be missing country code, try to add India code
            if len(clean_number) >= 8:
                clean_number = '91' + clean_number
                logger.info(f"   🇮🇳 Adding India country code 91 to short number: {clean_number}")
            else:
                logger.warning(f"   ⚠️ Invalid phone number format (too short): {phone_number}")
        elif len(clean_number) == 10:
            # Exactly 10 digits - assume it's an Indian number and add country code 91
            clean_number = '91' + clean_number
            logger.info(f"   🇮🇳 Adding India country code 91 to 10-digit number: {clean_number}")
        elif len(clean_number) > 15:
            # Too long - might be malformed, try to fix common issues
            logger.warning(f"   ⚠️ Phone number too long: {phone_number}")
            # If it starts with country code, keep only first 12 digits (country code + 10 digits)
            if clean_number.startswith('91') and len(clean_number) > 12:
                clean_number = clean_number[:12]
                logger.info(f"   ✂️ Truncated long Indian number: {clean_number}")
            elif len(clean_number) > 15:
                # Keep only first 15 digits
                clean_number = clean_number[:15]
                logger.info(f"   ✂️ Truncated very long number: {clean_number}")
        
        # GreenAPI expects format: 919876543210@c.us
        formatted_number = f"{clean_number}@c.us"
        logger.info(f"✅ Final formatted phone number: {phone_number} -> {formatted_number}")
        return formatted_number
    
    def check_status(self) -> Dict[str, Any]:
        """Check GreenAPI connection status"""
        if not self.api_available:
            return {
                'connected': False,
                'error': 'GreenAPI credentials not configured'
            }
        
        try:
            url = f"{self.base_url}/waInstance{self.instance_id}/getStateInstance/{self.token}"
            
            logger.info(f"📡 Checking GreenAPI status: {url}")
            response = requests.get(url, timeout=15)
            
            logger.info(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"📡 GreenAPI Status Response: {json.dumps(response_data, indent=2)}")
                
                state = response_data.get('stateInstance', 'unknown')
                return {
                    'connected': state == 'authorized',
                    'state': state,
                    'status': response_data,
                    'service': 'GreenAPI',
                    'endpoint': url
                }
            else:
                error_text = response.text
                logger.error(f"📡 GreenAPI Error Response: {error_text}")
                return {
                    'connected': False,
                    'error': f'GreenAPI HTTP {response.status_code}: {error_text}',
                    'service': 'GreenAPI',
                    'endpoint': url
                }
                
        except requests.exceptions.Timeout:
            logger.error("📡 GreenAPI request timeout")
            return {
                'connected': False,
                'error': 'GreenAPI request timeout (15 seconds)',
                'service': 'GreenAPI'
            }
        except Exception as e:
            logger.error(f"📡 GreenAPI status check error: {str(e)}")
            return {
                'connected': False,
                'error': f'GreenAPI status check error: {str(e)}',
                'service': 'GreenAPI'
            }
    
    def get_message_templates(self) -> Dict[str, str]:
        """
        Get predefined message templates for different enquiry scenarios
        
        Returns:
            Dict: Dictionary of template names and messages
        """
        return {
            'new_enquiry': """Hi {wati_name}👋 Welcome to Business Guru Loans!

Get ₹10 Lakhs in 24 hours for your business:

✅ 1% monthly interest (Lowest in market!)

✅ Zero collateral or CIBIL checks

✅ New startups welcome

Apply Now: https://tmis-business-guru.vercel.app/new-enquiry

✨ Special Benefits:

- 0% processing fees (First 50 applicants)

- Flexible repayment: 1-5 years

🏆 Trusted by 2,500+ businesses

📱 Ready to grow?
Apply Now: https://tmis-business-guru.vercel.app/new-enquiry

Your success journey begins now! 🚀

*Please click on any option below:*

🔗 Get Loan: https://wa.me/918106811285?text=Get%20Loan

🔗 Check Eligibility: https://wa.me/918106811285?text=Check%20Eligibility

🔗 More Details: https://wa.me/918106811285?text=More%20Details""",
            
            'new_enquiry_public_form': """Hi {wati_name}👋 Welcome to Business Guru Loans!

Get ₹10 Lakhs in 24 hours for your business:

✅ 1% monthly interest (Lowest in market!)

✅ Zero collateral or CIBIL checks

✅ New startups welcome


✨ Special Benefits:

- 0% processing fees (First 50 applicants)

- Flexible repayment: 1-5 years

🏆 Trusted by 2,500+ businesses


Your success journey begins now! 🚀

*Please click on any option below:*

🔗 Get Loan: https://wa.me/918106811285?text=Get%20Loan

🔗 Check Eligibility: https://wa.me/918106811285?text=Check%20Eligibility

🔗 More Details: https://wa.me/918106811285?text=More%20Details""",
            
            'no_gst': """Hii {wati_name} sir/madam! 🙏

We regret to inform you that we're unable to process your loan application at this time due to the absence of GST registration. GST registration is a mandatory requirement for our collateral loan services as it helps us verify your business credentials and compliance status. We recommend you to register for GST at the earliest convenience through the official portal. Once you've completed your GST registration, please contact us again so we can proceed with your application. 

Thank you for your understanding! 📋❌""",
            
            'gst_cancelled': """Hii {wati_name} sir/madam! 🙏

We've noticed that your GST status is currently showing as cancelled in our records. To proceed with your loan application, we require an active GST registration with proper compliance. We kindly request you to reactivate your GST by filling out your previous GST forms and completing all necessary formalities with the tax authorities. Once your GST status is active again, please inform us immediately so we can continue processing your application without any delays.

Thank you for your prompt attention to this matter! 📝🔄""",
            
            'will_share_doc': """Hii {wati_name} sir/madam! 🙏

Thank you for your interest in Business Guru! To proceed with verification of your loan application, we require the following documents:

1. Company/Business Registration
2. GST Document
3. Company Bank Account Details
4. Bank statement (6-12 months)
5. Website (Optional)
6. Owner's PAN & Aadhaar
7. Business PAN
8. Email ID & Mobile Number
9. IE Code (Optional)
10. Payment Gateway (Optional)
11. Business Photos (Name board, Products, Shop)

Please share these documents at your earliest convenience to avoid delays. 📂✅""",
            
            'doc_shared': """Hii {wati_name} sir/madam! 🙏

Thank you for sharing your documents with us! Our verification team is currently reviewing all the submitted documents to assess your eligibility for our collateral loan services. This comprehensive verification process typically takes 2-3 business days to complete. We'll notify you immediately if any additional documents are required or if there are any changes needed in the submitted documents. 

Rest assured, our team is working diligently to process your application as quickly as possible. 

Thank you for your patience! 📋🔍""",
            
            'verified_shortlisted': """Hii {wati_name} sir/madam! 🎉

Congratulations! Your account has been successfully verified and shortlisted for our collateral loan program. This is a significant milestone in your loan application process with Business Guru. Our dedicated account manager will contact you within 2 working days to discuss the next steps, including detailed loan terms, competitive interest rates, processing fees, and disbursement procedures. We understand your eagerness and assure you that we're committed to providing you with the best financial solutions for your business growth and success in the coming days.

We're excited to partner with you and support your business growth journey. 

Thank you! 🚀⭐""",
            
            'not_eligible': """Hii {wati_name} sir/madam! 🙏

Thank you for reaching out to Business Guru. After carefully reviewing your application and business profile for {business_nature}, we regret to inform you that we're unable to provide a loan at this time. Our decision is based on our current lending criteria, risk assessment policies, and internal evaluation process. 

We appreciate your interest in our services and encourage you to contact us again in the future as our policies may change. 

Thank you for understanding! 📉❌""",
            
            'no_msme': """Hii {wati_name} sir/madam! 🙏

We're unable to proceed with your loan application as an MSME certificate is required for our collateral loan services. The MSME certificate is essential for us to categorize your business accurately and determine appropriate loan terms and benefits. We recommend you to apply for an MSME certificate through the official government portal Udyam Registration. 

Once you've obtained your MSME certificate, please share it with us so we can move forward with your application process. 

Thank you for your cooperation! 📄🔄""",
            
            'aadhar_pan_mismatch': """Hii {wati_name} sir/madam! 🙏

During document verification, we found a mismatch between your Aadhaar and PAN card names. This discrepancy must be resolved before proceeding with your loan application. Please update your PAN card name to exactly match your Aadhaar card without any variations. Also, verify that your date of birth matches on both documents. If there's a mismatch in the date of birth, that needs to be corrected through the appropriate authorities. 

Once updated, please inform us so we can continue processing your application. 🔄📋""",
            
            'msme_gst_address_different': """Hii {wati_name} sir/madam! 🙏

Our verification team found an address mismatch between your GST and MSME certificates. For compliance purposes, these addresses need to be consistent in our records. We request you to update your MSME address to match exactly with your GST address as per official documentation. Please ensure all your business documents reflect the same address to avoid any processing delays. Once you've made the necessary updates to your MSME certificate, please notify us so we can proceed with your application. 

Thank you for your attention! 📍📝""",
            
            'will_call_back': """Hii {wati_name} sir/madam! 📞

Thank you for your interest in Business Guru's collateral loan services. We appreciate your time and interest in our financial solutions. Currently, our representative is engaged with other calls, but we value your inquiry and want to ensure you receive proper attention and personalized service. 

Please send a message to this number when you're available, and we'll call you back promptly to discuss your business loan requirements in detail. 

Thank you for your understanding! 🕐💬""",
            
            'personal_loan': """Hii {wati_name} sir/madam! 🙏

Thank you for reaching out to Business Guru. We appreciate your interest in our financial services. However, we want to inform you that we specialize exclusively in collateral business loans and do not provide personal loans at this time. 

Our expertise lies in supporting businesses with working capital, expansion, and equipment financing through secured loan options. If you have any business-related financing needs, we'd be happy to assist you. 

Thank you for understanding! 🏢❌""",
            
            'startup': """Hii {wati_name} sir/madam! 🙏

Thanks for reaching out to Business Guru. We appreciate your interest in our financial services. After careful consideration, we regret to inform you that we're currently unable to provide startup loans. Our collateral loan services are primarily designed for established businesses with proven track records and existing assets. 

We encourage you to revisit our services once your business has been operational for a longer period. If you have any other business financing requirements, please let us know. 

Thank you! 🚀.DataGridViewColumn""",
            
            'less_than_5_lakhs': """Hii {wati_name} sir/madam! 🙏

We'd like to inform you about our loan policy regarding application amounts. Business Guru provides collateral loans ranging from 5 Lakhs to 5 Crores. Unfortunately, we're unable to process loan applications for amounts less than 5 Lakhs as they fall outside our current lending framework. We recommend consolidating your requirements or considering our services when your financing needs align with our specified range for better financial solutions.

Thank you for your understanding! 💰.DataGridViewColumn""",
            
            'first_call_completed': """Hii {wati_name} sir/madam! 📞

We've attempted to reach you regarding your loan application but were unable to connect with you. Our team tried calling but there was no response and the call went unanswered. We believe it's important to discuss your application details and address any queries you might have. 

Please call us back at your earliest convenience so we can continue processing your application without any further delays. 

Thank you! 🕐🔁""",
            
            'second_call_completed': """Hii {wati_name} sir/madam! 📞

This is our second attempt to reach you regarding your loan application. Unfortunately, we were unable to connect with you again. Our team tried calling but there was no response and the call went unanswered. It's crucial that we discuss your application to ensure all requirements are met. 

We request you to call us back as soon as possible to avoid any delays in processing your application. 

Thank you for your attention! 🕓🔁""",
            
            'third_call_completed': """Hii {wati_name} sir/madam! 📞

This is our final attempt to reach you regarding your loan application. We've tried contacting you multiple times but have been unsuccessful in connecting with you. Our team has made several calls, but there has been no response and the calls remain unanswered. 

This is a critical step in your application process. Please call us back immediately to prevent cancellation of your application. 

Thank you! ⏰❗""",
            
            'switch_off': """Hii {wati_name} sir/madam! 📞

We've attempted to reach you regarding your loan application, but your phone number appears to be switched off. Our team tried calling but couldn't establish a connection. This prevents us from discussing important details about your application and addressing any questions you might have. 

Please switch on your phone and call us back at your earliest convenience to continue with your application process. 

Thank you! 📴🔁""",
            
            'not_connected': """Hii {wati_name} sir/madam! 📞

We've tried reaching you regarding your loan application, but your call is not connecting. Our team has made multiple attempts to call you, but the connection is not going through. This is preventing us from moving forward with your application and addressing any concerns you might have. 

Please check your network connectivity and call us back as soon as possible to continue processing your application. 

Thank you! 📶🔁""",
            
            'by_mistake': """Hii {wati_name} sir/madam! 🙏

We understand that your enquiry might have been submitted by mistake. No issues at all! We appreciate your transparency in informing us. Should you require any collateral loan services in the future, please don't hesitate to contact Business Guru. 

We're always here to support your business financing needs. Feel free to reach out to us anytime for any collateral loan requirements. 

Thank you and have a great day! 🌟😊"""
        }
    
    def send_staff_assignment_messages(self, enquiry_data: Dict[str, Any], staff_name: str) -> Dict[str, Any]:
        """
        Send three sequential messages when staff is assigned to an enquiry
        
        Args:
            enquiry_data (dict): Enquiry information
            staff_name (str): Name of the assigned staff member
            
        Returns:
            Dict: Result of message sending
        """
        try:
            mobile_number = enquiry_data.get('mobile_number')
            customer_name = enquiry_data.get('wati_name', 'Customer')
            
            if not mobile_number:
                logger.error("No mobile number provided in enquiry data")
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            # Message 1: Introduction
            message1 = f"""Hi Sir/Madam

This is {staff_name}

How can I help you

We provide collateral free loan for all kinds of businesses based on transactions

Loan from 5 lacs to 5 crores - GST is must 

Working Hours : 10.00AM - 6.00PM"""
            
            # Message 2: Business information request
            message2 = "Could you please tell us about your business and its nature"
            
            # Message 3: Loan amount request
            message3 = "And what is the loan amount you require"
            
            # Send messages sequentially
            messages = [message1, message2, message3]
            results = []
            
            for i, message in enumerate(messages, 1):
                logger.info(f"Sending staff assignment message {i} to {mobile_number}")
                result = self.send_message(mobile_number, message)
                results.append(result)
                
                # If any message fails, stop sending the rest
                if not result['success']:
                    logger.error(f"Failed to send staff assignment message {i}: {result.get('error')}")
                    return {
                        'success': False,
                        'error': f'Failed to send message {i}: {result.get("error")}',
                        'messages_sent': i,
                        'results': results
                    }
                
                # Add a small delay between messages to ensure proper delivery order
                import time
                time.sleep(1)
            
            logger.info(f"Successfully sent all staff assignment messages to {mobile_number}")
            return {
                'success': True,
                'messages_sent': 3,
                'results': results,
                'notification': f"✅ 3 WhatsApp messages sent successfully to {customer_name}"
            }
            
        except Exception as e:
            logger.error(f"Error in send_staff_assignment_messages: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }
    
    def send_enquiry_message(self, enquiry_data: Dict[str, Any], message_type: str = 'new_enquiry') -> Dict[str, Any]:
        """
        Send a message based on enquiry data and type
        
        Args:
            enquiry_data (dict): Enquiry information
            message_type (str): Type of message to send
            
        Returns:
            Dict: Result of message sending
        """
        try:
            templates = self.get_message_templates()
            
            if message_type not in templates:
                logger.error(f"Unknown message type: {message_type}")
                return {
                    'success': False,
                    'error': f'Unknown message type: {message_type}'
                }
            
            # Get message template
            message_template = templates[message_type]
            
            # Format message with enquiry data
            formatted_message = message_template.format(
                wati_name=enquiry_data.get('wati_name', 'Customer'),
                business_nature=enquiry_data.get('business_nature', 'your business')
            )
            
            # Send message
            mobile_number = enquiry_data.get('mobile_number')
            if not mobile_number:
                logger.error("No mobile number provided in enquiry data")
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            result = self.send_message(mobile_number, formatted_message)
            
            # Log the activity with more detail
            if result['success']:
                logger.info(f"✅ SUCCESS: Sent {message_type} message to {enquiry_data.get('wati_name')} at {mobile_number}")
                logger.info(f"   Message ID: {result.get('message_id', 'N/A')}")
                logger.info(f"   Service: {result.get('service', 'Unknown')}")
                # Add success notification
                result['notification'] = f"✅ WhatsApp message sent successfully to {enquiry_data.get('wati_name')}"
            else:
                error_msg = result.get('error', 'Unknown error')
                status_code = result.get('status_code', 'N/A')
                logger.error(f"❌ FAILED: Send {message_type} message to {mobile_number}")
                logger.error(f"   Status Code: {status_code}")
                logger.error(f"   Error: {error_msg}")
                logger.error(f"   Original Number: {result.get('original_phone_number', 'N/A')}")
                logger.error(f"   Formatted Number: {result.get('formatted_phone_number', 'N/A')}")
                
                # Check for quota exceeded error
                quota_exceeded = (
                    result.get('status_code') == 466 or 
                    result.get('quota_exceeded') or 
                    'quota exceeded' in error_msg.lower() or 
                    'monthly quota' in error_msg.lower() or
                    'limit reached' in error_msg.lower()
                )
                
                if quota_exceeded:
                    logger.warning(f"🚨 GREENAPI QUOTA LIMIT REACHED!")
                    logger.warning(f"   Monthly quota has been exceeded for instance {self.instance_id}")
                    logger.warning(f"   Test number {result.get('working_test_number', '8106811285')} still works")
                    logger.warning(f"   Solution: Upgrade at {result.get('upgrade_url', 'https://console.green-api.com')}")
                    result['notification'] = f"🚨 GreenAPI monthly quota exceeded! Test number {result.get('working_test_number', '8106811285')} still works. Upgrade at {result.get('upgrade_url', 'https://console.green-api.com')}"
                    result['quota_exceeded'] = True
                    result['working_test_number'] = '8106811285'
                    result['upgrade_url'] = 'https://console.green-api.com'
                else:
                    result['notification'] = f"❌ Failed to send WhatsApp message: {error_msg}"
            
            # Add helpful information for quota exceeded cases
            if result.get('quota_exceeded'):
                result['quota_info'] = {
                    'exceeded': True,
                    'working_test_number': '8106811285',
                    'upgrade_url': 'https://console.green-api.com',
                    'solutions': [
                        'Upgrade to paid GreenAPI plan',
                        'Wait for monthly quota reset',
                        'Use test number 8106811285 for testing'
                    ]
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_enquiry_message: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }
    
    def get_comment_message_type(self, comment: str) -> str:
        """
        Map comment to appropriate message type
        
        Args:
            comment (str): Comment from enquiry
            
        Returns:
            str: Message type to use
        """
        comment_lower = comment.lower().strip()
        
        # Define mappings for different comment types
        comment_mappings = {
            'no gst': 'no_gst',
            'gst cancelled': 'gst_cancelled',
            'will share doc': 'will_share_doc',
            'doc shared(yet to verify)': 'doc_shared',
            'doc shared': 'doc_shared',
            'verified(shortlisted)': 'verified_shortlisted',
            'verified shortlisted': 'verified_shortlisted',
            'verified': 'verified_shortlisted',
            'shortlisted': 'verified_shortlisted',
            'not eligible': 'not_eligible',
            'no msme': 'no_msme',
            'aadhar/pan name mismatch': 'aadhar_pan_mismatch',
            'msme/gst address different': 'msme_gst_address_different',
            'will call back': 'will_call_back',
            'personal loan': 'personal_loan',
            'start up': 'startup',
            'startup': 'startup',  # Handle both "Start Up" and "Startup"
            'asking less than 5 lakhs': 'less_than_5_lakhs',
            '1st call completed': 'first_call_completed',
            '2nd call completed': 'second_call_completed',
            '3rd call completed': 'third_call_completed',
            'switch off': 'switch_off',
            'not connected': 'not_connected',
            'by mistake': 'by_mistake'
        }
        
        # Check for exact matches first
        for key, value in comment_mappings.items():
            if key in comment_lower:
                return value
        
        # Default fallback
        return 'new_enquiry'
    
    def setup_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """
        Set up webhook URL for receiving incoming messages
        Note: This requires configuring the webhook in the GreenAPI dashboard
        """
        try:
            if not self.api_available:
                return {
                    'success': False,
                    'error': 'GreenAPI service not available'
                }
            
            logger.info(f"🔧 Setting up webhook URL: {webhook_url}")
            
            # For GreenAPI, webhooks are typically configured in the dashboard
            # But we can log the expected URL for reference
            logger.info(f"ℹ️  To configure webhook in GreenAPI dashboard:")
            logger.info(f"   1. Go to https://console.green-api.com")
            logger.info(f"   2. Select your instance")
            logger.info(f"   3. Go to Settings > Webhooks")
            logger.info(f"   4. Set Webhook URL to: {webhook_url}")
            logger.info(f"   5. Enable 'Incoming Message' webhook")
            
            return {
                'success': True,
                'message': 'Webhook setup instructions provided',
                'webhook_url': webhook_url,
                'instructions': [
                    'Go to https://console.green-api.com',
                    'Select your instance',
                    'Go to Settings > Webhooks',
                    'Set Webhook URL to the provided URL',
                    'Enable "Incoming Message" webhook'
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting up webhook: {str(e)}")
            return {
                'success': False,
                'error': f'Error setting up webhook: {str(e)}'
            }
    
    def test_single_number(self, number: str) -> Dict[str, Any]:
        """Test sending message to a single number via GreenAPI"""
        logger.info(f"\n🧪 Testing GreenAPI with {number}...")
        result = self.send_message(
            number, 
            f"🧪 GreenAPI Test - No OTP required! Message to {number}"
        )
        return result
    
    def test_multiple_numbers(self, numbers: list) -> Dict[str, Any]:
        """Test sending messages to multiple numbers via GreenAPI"""
        results = {}
        
        for number in numbers:
            logger.info(f"\n🧪 Testing GreenAPI with {number}...")
            result = self.send_message(
                number, 
                f"🧪 GreenAPI Test - No OTP required! Message to {number}"
            )
            results[number] = result
        
        return results

# Create global instance for enquiry system compatibility
try:
    logger.info("🚀 Creating GreenAPI WhatsApp Service instance...")
    greenapi_service = GreenAPIWhatsAppService()
    whatsapp_service = greenapi_service  # Alias for compatibility with enquiry_routes.py
    
    if greenapi_service.api_available:
        logger.info("✅ GreenAPI WhatsApp Service ready and available")
    else:
        logger.warning("⚠️ GreenAPI WhatsApp Service created but not available (missing credentials)")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize GreenAPI Service: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    greenapi_service = None
    whatsapp_service = None

if __name__ == "__main__":
    """Test the GreenAPI service"""
    if greenapi_service and greenapi_service.api_available:
        # Check status first
        status = greenapi_service.check_status()
        print(f"📡 GreenAPI Status: {status}")
        
        if status.get('connected'):
            test_numbers = [
                '918106811285',  # Your number
                '917569307720',  # Test number from error
                '917010905730',  # Test number
                '919876543210',  # Random test
            ]
            
            print("\n🚀 Testing GreenAPI WhatsApp Service (NO OTP REQUIRED)")
            print("=" * 60)
            
            results = greenapi_service.test_multiple_numbers(test_numbers)
            
            print(f"\n📊 GREENAPI RESULTS:")
            for number, result in results.items():
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                print(f"{number}: {status}")
                if not result['success']:
                    print(f"   Error: {result.get('error')}")
                else:
                    print(f"   ✅ No OTP required!")
        else:
            print("❌ GreenAPI not connected. Please check connection.")
            print(f"   State: {status.get('state', 'unknown')}")
    else:
        print("❌ GreenAPI service not available. Please configure credentials.")
        print("\n🔧 Your credentials are already configured!")
        print("   Instance ID: 7105335459")
        print("   Token: 3a0876a6822049bc...")
        print("   Status: Should be 'authorized' as shown in your image")