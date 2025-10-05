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
            return ''
        elif len(clean_number) > 15:
            # Too long - might be malformed
            logger.warning(f"   ⚠️ Phone number too long: {phone_number}")
            return ''
        
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
            
            # Format IE Code display - only show Yes if IE Code document is actually uploaded
            # Check if IE document exists in the documents field
            documents = client_data.get('documents', {})
            ie_code_display = "Yes" if 'ie_code_document' in documents and documents['ie_code_document'] else "No"
            
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
    
    def send_multiple_client_update_messages(self, client_data: Dict[str, Any], updated_fields: list, 
                                           old_client_data = None) -> list:
        """
        Send multiple WhatsApp messages when client details are updated
        
        Args:
            client_data (dict): Updated client information
            updated_fields (list): List of updated fields
            old_client_data (dict): Original client data before update (optional)
            
        Returns:
            list: List of results for each message sent
        """
        results = []
        
        if not self.api_available:
            return [{'success': False, 'error': 'WhatsApp service not available'}]
        
        try:
            # Get mobile number
            mobile_number = client_data.get('mobile_number')
            if not mobile_number:
                return [{'success': False, 'error': 'No mobile number provided'}]
            
            # Format phone number
            formatted_number = self.format_phone_number(mobile_number)
            if not formatted_number:
                return [{'success': False, 'error': 'Invalid mobile number format'}]
            
            # Get client details
            legal_name = client_data.get('legal_name', 'Sir/Madam')
            
            # Send messages for each type of change
            
            # Check for user_email updates
            if 'user_email' in updated_fields:
                old_email = old_client_data.get('user_email', '') if old_client_data else ''
                new_email = client_data.get('user_email', '')
                
                if old_email and new_email and old_email != new_email:
                    message = f"""Hii {legal_name} sir/madam, 

Your mail was update successfully from ({old_email} to {new_email}). 

Thank you for keeping your information up to date with us!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                elif new_email and (not old_email or old_email != new_email):
                    message = f"""Hii {legal_name} sir/madam, 

Your New mail ({new_email}) was update successfully . 

Thank you !"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
            
            # Check for company_email updates
            if 'company_email' in updated_fields:
                old_email = old_client_data.get('company_email', '') if old_client_data else ''
                new_email = client_data.get('company_email', '')
                
                if old_email and new_email and old_email != new_email:
                    message = f"""Hii {legal_name} sir/madam, 

Your mail was update successfully from ({old_email} to {new_email}). 

Thank you for keeping your information up to date with us!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                elif new_email and (not old_email or old_email != new_email):
                    message = f"""Hii {legal_name} sir/madam, 

Your New mail ({new_email}) was update successfully . 

Thank you !"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
            
            # Check for optional mobile number updates
            if 'optional_mobile_number' in updated_fields:
                optional_mobile = client_data.get('optional_mobile_number', '')
                old_optional_mobile = old_client_data.get('optional_mobile_number', '') if old_client_data else ''
                
                # Only send message if there's actually a new optional mobile number
                if optional_mobile and (not old_optional_mobile or old_optional_mobile != optional_mobile):
                    message = f"""Hii {legal_name} sir/madam, 

Your alternate mobile number ({optional_mobile}) was added successfully . 

Thank you for keeping your information up to date with us!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
            
            # Check for website updates
            if 'website' in updated_fields:
                old_website = old_client_data.get('website', '') if old_client_data else ''
                new_website = client_data.get('website', '')
                
                if old_website and new_website and old_website != new_website:
                    message = f"""Hii {legal_name} sir/madam, 

Your website was update successfully from ({old_website} to {new_website}). 

Thank you !"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                elif new_website and (not old_website or old_website != new_website):
                    message = f"""Hii {legal_name} sir/madam, 

Your New Website ({new_website}) was created successfully . 

Thank you !"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
            
            # Check for new current account
            # Send notification when new_current_account is set to 'Yes'
            # This should happen regardless of whether bank details are being updated in the same request
            if 'new_current_account' in updated_fields:
                current_value = client_data.get('new_current_account', '')
                old_value = old_client_data.get('new_current_account', '') if old_client_data else ''
                
                # Only send message if changed from No/empty to yes (check both 'yes' and 'Yes')
                if current_value.lower() == 'yes' and old_value.lower() != 'yes':
                    new_bank_name = client_data.get('new_bank_name', 'N/A')
                    new_account_name = client_data.get('new_account_name', 'N/A')
                    new_bank_account_number = client_data.get('new_bank_account_number', 'N/A')
                    new_ifsc_code = client_data.get('new_ifsc_code', 'N/A')
                    
                    message = f"""Hii {legal_name} sir/madam, 

Your New current account was added successfully. 

Your current account details are:

New Bank name: {new_bank_name}

New Account name: {new_account_name}

New bank account number: {new_bank_account_number}

New IFSC code: {new_ifsc_code}

Please check all details are correct! If any mistake means please contact us.

Thank you!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                    logger.info(f"New current account notification sent for {legal_name}")
                else:
                    logger.info(f"New current account not changed to 'yes' or already was 'yes', not sending notification for {legal_name}")
            
            # Check for IE Code document uploads - CONSOLIDATED LOGIC TO PREVENT DUPLICATES
            # Only check once for IE document uploads to prevent duplicate messages
            ie_document_uploaded = False
            
            # Check if IE Code document was uploaded (either through 'ie_code' field or 'documents' field)
            if ('ie_code' in updated_fields or 'documents' in updated_fields) and not ie_document_uploaded:
                documents = client_data.get('documents', {})
                old_documents = old_client_data.get('documents', {}) if old_client_data else {}
                
                # Send message only if IE document was actually uploaded and is new
                if ('ie_code_document' in documents and documents['ie_code_document'] and
                    ('ie_code_document' not in old_documents or not old_documents['ie_code_document'])):
                    
                    message = f"""Hii {legal_name} sir/madam, 

Your IE Code has been successfully completed. 

Thank you! For further any update we will update you."""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                    ie_document_uploaded = True
                    logger.info(f"IE Code document uploaded successfully, notification sent for {legal_name}")
                else:
                    logger.info(f"No new IE Code document uploaded or already existed, not sending notification for {legal_name}")
            
            # Check for payment gateway status updates
            if 'payment_gateways_status' in updated_fields:
                payment_gateways_status = client_data.get('payment_gateways_status', {})
                old_payment_gateways_status = old_client_data.get('payment_gateways_status', {}) if old_client_data else {}
                
                # Find newly approved gateways (changed from not approved to approved)
                newly_approved_gateways = []
                newly_rejected_gateways = []
                newly_added_gateways = []  # For general payment gateway additions
                
                for gateway, new_status in payment_gateways_status.items():
                    old_status = old_payment_gateways_status.get(gateway, 'pending')
                    # Only send message if status actually changed
                    if old_status != new_status:
                        if new_status == 'approved':
                            newly_approved_gateways.append(gateway)
                        elif new_status == 'rejected' or new_status == 'not_approved':
                            newly_rejected_gateways.append(gateway)
                    # Check for newly added gateways (when old status was not present)
                    elif old_status == 'pending' and gateway not in old_payment_gateways_status:
                        newly_added_gateways.append(gateway)
                
                user_email = client_data.get('user_email', 'your registered email')
                
                # Send approval messages
                if newly_approved_gateways:
                    approved_gateways_str = ", ".join(newly_approved_gateways)
                    message = f"""Hii {legal_name} sir/madam, 

Congratulations! Your loan has been approved from ({approved_gateways_str}). 

You will receive a detailed email to your registered email ({user_email}) with all the loan details, terms, and next steps.

If you have any queries, please reach us.

Thank you!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                
                # Send rejection messages
                if newly_rejected_gateways:
                    rejected_gateways_str = ", ".join(newly_rejected_gateways)
                    message = f"""Hii {legal_name} sir/madam, 

Unfortunately! Your loan has been not approved from ({rejected_gateways_str}). 

No need to worry we try another payment gateway, once any new update we will update you

If you have any queries, please reach us.

Thank you!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
                
                # Send general payment gateway update message when gateways are added but not yet approved/rejected
                if 'payment_gateways' in updated_fields and not newly_approved_gateways and not newly_rejected_gateways:
                    current_payment_gateways = client_data.get('payment_gateways', [])
                    old_payment_gateways = old_client_data.get('payment_gateways', []) if old_client_data else []
                    
                    # Only send message if there are new gateways (not already selected)
                    new_gateways = [gateway for gateway in current_payment_gateways if gateway not in old_payment_gateways]
                    if new_gateways:
                        gateways_list = ", ".join(new_gateways)
                        message = f"""Hii {legal_name} sir/madam, 

Selected payment gateway options ({gateways_list}) have been applied successfully. 

Once Loan Approved, you will get mail to your registered email. 

If any queries please reach us. 

Thank you!"""
                        result = self.whatsapp_service.send_message(formatted_number, message)
                        results.append(result)
            
            # Also check for payment gateways being added without status changes
            elif 'payment_gateways' in updated_fields:
                # Check if payment gateways have actually changed
                current_payment_gateways = client_data.get('payment_gateways', [])
                old_payment_gateways = old_client_data.get('payment_gateways', []) if old_client_data else []
                
                # Only send message if there are new gateways (not already selected)
                new_gateways = [gateway for gateway in current_payment_gateways if gateway not in old_payment_gateways]
                if new_gateways:
                    gateways_list = ", ".join(new_gateways)
                    message = f"""Hii {legal_name} sir/madam, 

Selected payment gateway options ({gateways_list}) have been applied successfully. 

Once Loan Approved, you will get mail to your registered email. 

If any queries please reach us. 

Thank you!"""
                    result = self.whatsapp_service.send_message(formatted_number, message)
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in send_multiple_client_update_messages: {str(e)}")
            return [{'success': False, 'error': f'Error: {str(e)}'}]
    
    def send_client_update_message(self, client_data: Dict[str, Any], update_type: str, 
                                 updated_fields: list = [], old_client_data = None) -> Dict[str, Any]:
        """
        Send WhatsApp message when client details are updated
        
        Args:
            client_data (dict): Client information
            update_type (str): Type of update
            updated_fields (list): List of updated fields
            old_client_data (dict): Original client data before update (optional)
            
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
            
            # Create appropriate message based on update type
            if update_type == 'personal_info':
                # Personal information update - check for specific fields
                if updated_fields:
                    # Check for user_email updates
                    if 'user_email' in updated_fields:
                        old_email = old_client_data.get('user_email', '') if old_client_data else ''
                        new_email = client_data.get('user_email', '')
                        if old_email and new_email and old_email != new_email:
                            message = f"""Hii {legal_name} sir/madam, 

Your mail was update successfully from ({old_email} to {new_email}). 

Thank you for keeping your information up to date with us!"""
                        elif new_email and (not old_email or old_email != new_email):
                            message = f"""Hii {legal_name} sir/madam, 

Your New mail ({new_email}) was update successfully . 

Thank you !"""
                        else:
                            message = f"""Hii {legal_name} sir/madam, 

Your email was updated successfully. 

Thank you for keeping your information up to date with us!"""
                    # Check for company_email updates
                    elif 'company_email' in updated_fields:
                        old_email = old_client_data.get('company_email', '') if old_client_data else ''
                        new_email = client_data.get('company_email', '')
                        if old_email and new_email and old_email != new_email:
                            message = f"""Hii {legal_name} sir/madam, 

Your mail was update successfully from ({old_email} to {new_email}). 

Thank you for keeping your information up to date with us!"""
                        elif new_email and (not old_email or old_email != new_email):
                            message = f"""Hii {legal_name} sir/madam, 

Your New mail ({new_email}) was update successfully . 

Thank you !"""
                        else:
                            message = f"""Hii {legal_name} sir/madam, 

Your email was updated successfully. 

Thank you for keeping your information up to date with us!"""
                    # Check for optional mobile number updates
                    elif 'optional_mobile_number' in updated_fields:
                        optional_mobile = client_data.get('optional_mobile_number', '')
                        old_optional_mobile = old_client_data.get('optional_mobile_number', '') if old_client_data else ''
                        if optional_mobile and (not old_optional_mobile or old_optional_mobile != optional_mobile):
                            message = f"""Hii {legal_name} sir/madam, 

Your alternate mobile number ({optional_mobile}) was added successfully . 

Thank you for keeping your information up to date with us!"""
                        else:
                            message = f"""Hii {legal_name} sir/madam, 

Your alternate mobile number was updated successfully. 

Thank you for keeping your information up to date with us!"""
                    # Check for website updates
                    elif 'website' in updated_fields:
                        old_website = old_client_data.get('website', '') if old_client_data else ''
                        new_website = client_data.get('website', '')
                        if old_website and new_website and old_website != new_website:
                            message = f"""Hii {legal_name} sir/madam, 

Your website was update successfully from ({old_website} to {new_website}). 

Thank you !"""
                        elif new_website and (not old_website or old_website != new_website):
                            message = f"""Hii {legal_name} sir/madam, 

Your New Website ({new_website}) was created successfully . 

Thank you !"""
                        else:
                            message = f"""Hii {legal_name} sir/madam, 

Your website was updated successfully. 

Thank you !"""
                    else:
                        # General personal info update
                        fields_str = ", ".join(updated_fields)
                        message = f"""Hii {legal_name} sir/madam, 

Your details for ({fields_str}) have been successfully updated. 

Thank you for keeping your information up to date with us!"""
                else:
                    # No specific fields updated
                    message = f"""Hii {legal_name} sir/madam, 

Your personal information has been updated successfully. 

Thank you for keeping your information up to date with us!"""
                
            elif update_type == 'ie_document':
                # IE Document uploaded - check if IE document actually exists in documents
                documents = client_data.get('documents', {})
                # Also check in old client data for comparison
                old_documents = old_client_data.get('documents', {}) if old_client_data else {}
                
                # Send message only if IE document was actually uploaded
                if 'ie_code_document' in documents and documents['ie_code_document']:
                    # Check if this is a new upload (not previously present)
                    if 'ie_code_document' not in old_documents or not old_documents['ie_code_document']:
                        message = f"""Hii {legal_name} sir/madam, 

Your IE Code has been successfully uploaded. 

Thank you for providing all the required documents!"""
                        result = self.whatsapp_service.send_message(formatted_number, message)
                        return result
                    else:
                        # Document was already present, don't send duplicate message
                        logger.info(f"IE Code document already existed, not sending duplicate notification for {legal_name}")
                        return {'success': True, 'message': 'No new IE document uploaded'}
                else:
                    # No IE document was actually uploaded
                    logger.info(f"No IE Code document uploaded, not sending notification for {legal_name}")
                    return {'success': True, 'message': 'No IE document to send notification for'}
            
            elif update_type == 'new_current_account':
                # New current account added
                new_bank_name = client_data.get('new_bank_name', 'N/A')
                new_account_name = client_data.get('new_account_name', 'N/A')
                new_bank_account_number = client_data.get('new_bank_account_number', 'N/A')
                new_ifsc_code = client_data.get('new_ifsc_code', 'N/A')
                
                message = f"""Hii {legal_name} sir/madam, 

Your New current was added successfully . 

your current account details are 

New Bank name : {new_bank_name}

New Account name : {new_account_name}

new bank account number : {new_bank_account_number}

new IFSC code : {new_ifsc_code}

please check all details are correct! if any mistake means please contact us

Thank you !"""
                
            elif update_type == 'payment_gateway' or update_type == 'payment_gateway_approval':
                # Payment gateway configuration
                payment_gateways = client_data.get('payment_gateways', [])
                gateways_list = ", ".join(payment_gateways) if payment_gateways else "None"
                
                # Check if any gateway status changed to approved or rejected
                payment_gateways_status = client_data.get('payment_gateways_status', {})
                old_payment_gateways_status = old_client_data.get('payment_gateways_status', {}) if old_client_data else {}
                
                # Find newly approved/rejected gateways
                newly_approved_gateways = []
                newly_rejected_gateways = []
                
                for gateway, new_status in payment_gateways_status.items():
                    old_status = old_payment_gateways_status.get(gateway, 'pending')
                    # Only send message if status actually changed
                    if old_status != new_status:
                        if new_status == 'approved':
                            newly_approved_gateways.append(gateway)
                        elif new_status == 'rejected' or new_status == 'not_approved':
                            newly_rejected_gateways.append(gateway)
                
                if newly_approved_gateways:
                    # Loan approved message
                    approved_gateways_str = ", ".join(newly_approved_gateways)
                    message = f"""Hii {legal_name} sir/madam, 

Congratulations! Your loan has been approved from ({approved_gateways_str}). 

You will receive a detailed email to your registered email ({user_email}) with all the loan details, terms, and next steps.

If you have any queries, please reach us.

Thank you!"""
                elif newly_rejected_gateways:
                    # Loan not approved message
                    rejected_gateways_str = ", ".join(newly_rejected_gateways)
                    message = f"""Hii {legal_name} sir/madam, 

Unfortunately! Your loan has been not approved from ({rejected_gateways_str}). 

No need to worry we try another payment gateway, once any new update we will update you

If you have any queries, please reach us.

Thank you!"""
                else:
                    # General payment gateway update
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