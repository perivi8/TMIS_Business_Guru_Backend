#!/usr/bin/env python3
"""
Comment Templates Service - WhatsApp templates for client comments
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentTemplatesService:
    """Service to generate WhatsApp templates for client comments"""
    
    def __init__(self):
        logger.info("🔧 Comment Templates Service initialized")
    
    def get_comment_template(self, comment: str, legal_name: str) -> Optional[str]:
        """
        Get WhatsApp template message based on comment selection
        
        Args:
            comment (str): Selected comment from dropdown
            legal_name (str): Client's legal name
            
        Returns:
            str: Template message or None if comment not found
        """
        # Default name if not provided
        name = legal_name if legal_name else "Sir/Madam"
        
        templates = {
            "Not Interested": f"""hii {name} sir/madam , thanks for reaching us you shared all your documnets , all are verified , unfortunality you are not interested this loan process , In future if you want loan means fell free to contact us , Thank you""",
            
            "Will call back": f"""hii {name} sir/madam ,Thank you for your valuable time. Whenever you are free, kindly get in touch with us by call or message., Thank You """,
            
            "1st call completed": f"""hii {name} sir/madam , We attempted to contact you regarding your loan application, as your profile has been shortlisted. However, our team was unable to reach you, and the 1st call went unanswered.We would like to discuss the next steps in your loan process to ensure there are no delays in completing your application. Kindly return our call or reach out to us at your earliest convenience.Thank you for your time and cooperation.""",
            
            "2nd call completed": f"""hii {name} sir/madam , We attempted to contact you regarding your loan application, as your profile has been shortlisted. However, our team was unable to reach you, and the 2nd call went unanswered.We would like to discuss the next steps in your loan process to ensure there are no delays in completing your application. Kindly return our call or reach out to us at your earliest convenience.Thank you for your time and cooperation.""",
            
            "3rd call completed": f"""hii {name} sir/madam , We attempted to contact you regarding your loan application, as your profile has been shortlisted. However, our team was unable to reach you, and the 3rd call went unanswered.We would like to discuss the next steps in your loan process to ensure there are no delays in completing your application. Kindly return our call or reach out to us at your earliest convenience.Thank you for your time and cooperation.""",
            
            "4th call completed": f"""hii {name} sir/madam , We attempted to contact you regarding your loan application, as your profile has been shortlisted. However, our team was unable to reach you, and the 4th call went unanswered.We would like to discuss the next steps in your loan process to ensure there are no delays in completing your application. Kindly return our call or reach out to us at your earliest convenience.Thank you for your time and cooperation.""",
            
            "5th call completed": f"""hii {name} sir/madam , We attempted to contact you regarding your loan application, as your profile has been shortlisted. However, our team was unable to reach you, and our fifth call went unanswered. We would like to discuss the next steps in your loan process to avoid any delay in completing your application. Kindly return our call or reach out to us at your earliest convenience. Please note, this will be our final attempt to contact you. If we do not receive a response within the next 24 hours, your application will be considered withdrawn/rejected. Thank you for your time and cooperation.""",
            
            "rejected": f"""hii {name} sir/madam , We attempted to contact you multiple times regarding your loan application, as your profile had been shortlisted. However, we did not receive any response within the given timeframe.As a result, we regret to inform you that your loan application has been closed/rejected due to non-response. If you wish to reapply or discuss this further, please feel free to contact us, and our team will be happy to assist you with a new application process. Thank you for your interest and time. """,
            
            "cash free login completed": f"""hii {name} sir/madam ,We're pleased to inform you that your Cashfree login has been successfully completed.Our team will review the details and update you shortly regarding the next steps in the process.Thank you for your cooperation and patience.""",
            
            "share product images": f"""hii {name} sir/madam ,We hope you're doing well. Could you please share the images of your products at your earliest convenience? These will help us proceed with the next steps of the process. Kindly ensure the images are clear and of good quality for better review.Thank you for your cooperation.""",
            
            "share signature": f"""hii {name} sir/madam ,We hope you're doing well. Kindly share your signature at your earliest convenience to complete the documentation process.Please ensure the signature is clear and matches your official records (you may share a scanned copy or a clear photo).Thank you for your prompt attention."""
        }
        
        # Return template if found, otherwise None
        return templates.get(comment)
    
    def send_comment_notification(self, whatsapp_service, client_data: Dict[str, Any], comment: str) -> Dict[str, Any]:
        """
        Send WhatsApp notification for comment selection
        
        Args:
            whatsapp_service: WhatsApp service instance
            client_data (dict): Client information
            comment (str): Selected comment
            
        Returns:
            Dict: Result of message sending
        """
        try:
            # Get mobile number
            mobile_number = client_data.get('mobile_number')
            if not mobile_number:
                return {
                    'success': False,
                    'error': 'No mobile number provided'
                }
            
            # Get client details
            legal_name = client_data.get('legal_name', 'Sir/Madam')
            
            # Get template message
            message = self.get_comment_template(comment, legal_name)
            if not message:
                return {
                    'success': False,
                    'error': f'No template found for comment: {comment}'
                }
            
            # Format phone number
            formatted_number = whatsapp_service.format_phone_number(mobile_number)
            if not formatted_number:
                return {
                    'success': False,
                    'error': 'Invalid mobile number format'
                }
            
            # Send message
            result = whatsapp_service.whatsapp_service.send_message(formatted_number, message)
            
            # Log the activity
            if result['success']:
                logger.info(f"Sent comment notification for '{comment}' to {legal_name} at {mobile_number}")
            else:
                logger.error(f"Failed to send comment notification for '{comment}' to {mobile_number}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in send_comment_notification: {str(e)}")
            return {
                'success': False,
                'error': f'Error: {str(e)}'
            }