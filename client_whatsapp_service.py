#!/usr/bin/env python3
"""
Client WhatsApp Service - Send messages for client creation and updates
Uses GreenAPI.com service which connects to regular WhatsApp
"""

import os
import logging
from typing import Dict, Any
from greenapi_whatsapp_service import GreenAPIWhatsAppService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClientWhatsAppService:
    """WhatsApp service for client notifications"""
    
    def __init__(self):
        self.whatsapp_service = GreenAPIWhatsAppService()
        self.api_available = self.whatsapp_service.api_available
        logger.info(f"🔧 Client WhatsApp Service initialized: {'Available' if self.api_available else 'Not Available'}")
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format phone number for WhatsApp"""
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # Handle different cases based on number length
        if len(clean_number) == 10:
            # Exactly 10 digits - assume it's an Indian number and add country code 91
            clean_number = '91' + clean_number
        elif len(clean_number) < 10:
            # Invalid number
            logger.warning(f"   ⚠️ Invalid phone number format (too short): {phone_number}")
            return None
        elif len(clean_number) > 15:
            # Too long - might be malformed
            logger.warning(f"   ⚠️ Phone number too long: {phone_number}")
            return None
        
        return clean_number
    
    def send_new_client_message(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message when new client is added
        
        Args:
            client_data (dict): Client information
            
        Returns:
            Dict: Result of message sending
        """
        if not self.api_available:
            return {
                'success': False,
                'error': 'WhatsApp service not available'
            }
        
        try:
            # Get mobile number
            mobile_number = client_data.get('mobile_number')
            if not mobile_number:
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            # Format phone number
            formatted_number = self.format_phone_number(mobile_number)
            if not formatted_number:
                return {
                    'success': False,
                    'error': 'Invalid mobile number format'
                }
            
            # Get client details
            legal_name = client_data.get('legal_name', 'Sir/Madam')
            registration_number = client_data.get('registration_number', 'N/A')
            trade_name = client_data.get('trade_name', 'N/A')
            gst_status = client_data.get('gst_status', 'N/A')
            constitution_type = client_data.get('constitution_type', 'N/A')
            address = client_data.get('address', 'N/A')
            district = client_data.get('district', 'N/A')
            state = client_data.get('state', 'N/A')
            pincode = client_data.get('pincode', 'N/A')
            required_loan_amount = client_data.get('required_loan_amount', 'N/A')
            loan_purpose = client_data.get('loan_purpose', 'N/A')
            ie_code = client_data.get('ie_code', 'N/A')
            website = client_data.get('website', 'N/A')
            
            # Format IE Code display
            ie_code_display = "Yes" if ie_code and ie_code.strip() else "No"
            
            # Format website display
            website_display = website if website and website.strip() else "No"
            
            # Create message template
            message = f"""Hi {legal_name} sir/madam, 

Thanks for reaching us for Business Loan. 

Your details are:
- Registration Number: {registration_number}
- Trade Name / Business name: {trade_name}
- GST Registration status: {gst_status}
- Business Constitution type: {constitution_type}
- Address: {address}
- District: {district}
- State: {state}
- Pincode: {pincode}
- Required loan amount: {required_loan_amount}
- Loan Purpose: {loan_purpose}
- IE Code: {ie_code_display}
- Website URL: {website_display}

Please check all details are correct! If any mistakes or any update means contact us.

After we send all your documents to our account manager, sir/madam will call you in 2-4 Business days. They will explain all Loan Process. 

Everything if you have any Queries means contact us.

Thank you!"""

            # Send message
            result = self.whatsapp_service.send_message(formatted_number, message)
            
            # Log the activity
            if result['success']:
                logger.info(f"Sent new client message to {legal_name} at {mobile_number}")
            else:
                logger.error(f"Failed to send new client message to {mobile_number}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_new_client_message: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }
    
    def send_client_update_message(self, client_data: Dict[str, Any], update_type: str, 
                                 updated_fields: list = None) -> Dict[str, Any]:
        """
        Send WhatsApp message when client details are updated
        
        Args:
            client_data (dict): Client information
            update_type (str): Type of update
            updated_fields (list): List of updated fields
            
        Returns:
            Dict: Result of message sending
        """
        if not self.api_available:
            return {
                'success': False,
                'error': 'WhatsApp service not available'
            }
        
        try:
            # Get mobile number
            mobile_number = client_data.get('mobile_number')
            if not mobile_number:
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            # Format phone number
            formatted_number = self.format_phone_number(mobile_number)
            if not formatted_number:
                return {
                    'success': False,
                    'error': 'Invalid mobile number format'
                }
            
            # Get client details
            legal_name = client_data.get('legal_name', 'Sir/Madam')
            
            # Create appropriate message based on update type
            if update_type == 'personal_info':
                # Personal information update
                message = f"""Hii {legal_name} sir/madam, 

Your new update details have been successfully saved. 

Thank you for keeping your information up to date with us!"""
                
            elif update_type == 'ie_document':
                # IE Document uploaded
                message = f"""Hii {legal_name} sir/madam, 

Your IE Code has been successfully uploaded. 

Thank you for providing all the required documents!"""
                
            elif update_type == 'payment_gateway':
                # Payment gateway configuration
                payment_gateways = client_data.get('payment_gateways', [])
                gateways_list = ", ".join(payment_gateways) if payment_gateways else "None"
                
                message = f"""Hii {legal_name} sir/madam, 

Selected payment gateway options ({gateways_list}) have been applied successfully. 

Once Loan Approved, you will get mail to your registered email. 

If any queries please reach us. 

Thank you!"""
                
            elif update_type == 'general_update':
                # General update with specific fields
                if updated_fields:
                    fields_str = ", ".join(updated_fields)
                    message = f"""Hii {legal_name} sir/madam, 

Your details for ({fields_str}) have been successfully updated. 

Thank you for keeping your information up to date with us!"""
                else:
                    message = f"""Hii {legal_name} sir/madam, 

Your details have been successfully updated. 

Thank you for keeping your information up to date with us!"""
            else:
                # Default message
                message = f"""Hii {legal_name} sir/madam, 

Your details have been successfully updated. 

Thank you for keeping your information up to date with us!"""
            
            # Send message
            result = self.whatsapp_service.send_message(formatted_number, message)
            
            # Log the activity
            if result['success']:
                logger.info(f"Sent client update message ({update_type}) to {legal_name} at {mobile_number}")
            else:
                logger.error(f"Failed to send client update message to {mobile_number}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_client_update_message: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }
    
    def send_loan_approved_message(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send WhatsApp message when loan is approved
        
        Args:
            client_data (dict): Client information
            
        Returns:
            Dict: Result of message sending
        """
        if not self.api_available:
            return {
                'success': False,
                'error': 'WhatsApp service not available'
            }
        
        try:
            # Get mobile number
            mobile_number = client_data.get('mobile_number')
            if not mobile_number:
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            # Format phone number
            formatted_number = self.format_phone_number(mobile_number)
            if not formatted_number:
                return {
                    'success': False,
                    'error': 'Invalid mobile number format'
                }
            
            # Get client details
            legal_name = client_data.get('legal_name', 'Sir/Madam')
            user_email = client_data.get('user_email', 'your registered email')
            
            # Create message
            message = f"""Hii {legal_name} sir/madam, 

Congratulations! Your loan has been approved. 

You will receive a detailed email to your registered email ({user_email}) with all the loan details, terms, and next steps.

If you have any queries, please reach us.

Thank you!"""
            
            # Send message
            result = self.whatsapp_service.send_message(formatted_number, message)
            
            # Log the activity
            if result['success']:
                logger.info(f"Sent loan approved message to {legal_name} at {mobile_number}")
            else:
                logger.error(f"Failed to send loan approved message to {mobile_number}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_loan_approved_message: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }

# Create global instance
try:
    logger.info("🚀 Creating Client WhatsApp Service instance...")
    client_whatsapp_service = ClientWhatsAppService()
    
    if client_whatsapp_service.api_available:
        logger.info("✅ Client WhatsApp Service ready and available")
    else:
        logger.warning("⚠️ Client WhatsApp Service created but not available (missing credentials)")
        
except Exception as e:
    logger.error(f"❌ Failed to initialize Client WhatsApp Service: {e}")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    client_whatsapp_service = None

if __name__ == "__main__":
    """Test the Client WhatsApp service"""
    if client_whatsapp_service and client_whatsapp_service.api_available:
        # Test with sample data
        sample_client = {
            'legal_name': 'John Doe',
            'mobile_number': '919876543210',
            'registration_number': 'REG123456',
            'trade_name': 'Doe Enterprises',
            'gst_status': 'Active',
            'constitution_type': 'Private Limited',
            'address': '123 Main Street',
            'district': 'Mumbai',
            'state': 'Maharashtra',
            'pincode': '400001',
            'required_loan_amount': '500000',
            'loan_purpose': 'Business Expansion',
            'ie_code': 'IE123456',
            'website': 'www.doeenterprises.com'
        }
        
        print("🚀 Testing Client WhatsApp Service...")
        result = client_whatsapp_service.send_new_client_message(sample_client)
        print(f"Result: {result}")
    else:
        print("❌ Client WhatsApp service not available.")