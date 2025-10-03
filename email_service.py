import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

class EmailService:
    def __init__(self):
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def send_client_update_notification(self, client_data, admin_name, tmis_users, update_type="updated"):
        """
        Send email notification when admin updates a client
        
        Args:
            client_data: Dictionary containing client information
            admin_name: Name of the admin who made the changes
            tmis_users: List of users with tmis.* email addresses
            update_type: Type of update (updated, status_changed, etc.)
        """
        try:
            print(f"Starting email notification process...")
            print(f"SMTP Configuration - Email: {self.smtp_email}, Server: {self.smtp_server}, Port: {self.smtp_port}")
            
            # Validate SMTP configuration
            if not self.smtp_email or not self.smtp_password:
                self.logger.error("SMTP email or password not configured")
                print("ERROR: SMTP email or password not configured in .env file")
                return False
            
            # Prepare email recipients - separate TMIS users from client emails
            tmis_recipients = []
            client_recipients = []
            
            # Add tmis.* users
            print(f"Processing {len(tmis_users)} TMIS users...")
            for user in tmis_users:
                if user.get('email') and user['email'].startswith('tmis.'):
                    tmis_recipients.append(user['email'])
                    print(f"Added TMIS user: {user['email']}")
            
            # Add client emails if available
            if client_data.get('user_email'):
                client_recipients.append(client_data['user_email'])
                print(f"Added client user email: {client_data['user_email']}")
            
            if client_data.get('company_email') and client_data['company_email'] != client_data.get('user_email'):
                client_recipients.append(client_data['company_email'])
                print(f"Added client company email: {client_data['company_email']}")
            
            print(f"TMIS recipients: {len(tmis_recipients)} - {tmis_recipients}")
            print(f"Client recipients: {len(client_recipients)} - {client_recipients}")
            
            success = True
            
            # Send emails to TMIS users with internal template
            if tmis_recipients:
                subject = f"Client {update_type.title()}: {client_data.get('legal_name', 'Unknown Client')}"
                html_body = self._create_tmis_email_template(client_data, admin_name, update_type)
                
                tmis_success = self._send_email(tmis_recipients, subject, html_body)
                if tmis_success:
                    print(f"SUCCESS: TMIS email sent to {len(tmis_recipients)} recipients")
                else:
                    print("ERROR: Failed to send TMIS email")
                    success = False
            
            # Send emails to client with client-friendly template
            if client_recipients:
                subject = f"Your Business Application Status Update"
                html_body = self._create_client_email_template(client_data, update_type)
                
                client_success = self._send_email(client_recipients, subject, html_body)
                if client_success:
                    print(f"SUCCESS: Client email sent to {len(client_recipients)} recipients")
                else:
                    print("ERROR: Failed to send client email")
                    success = False
            
            if not tmis_recipients and not client_recipients:
                self.logger.warning("No recipients found for client update notification")
                print("WARNING: No recipients found for email notification")
                return False
            
            if success:
                self.logger.info(f"Client update notifications sent successfully")
                print(f"SUCCESS: All email notifications sent successfully")
            else:
                self.logger.error("Some email notifications failed")
                print("ERROR: Some email notifications failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending client update notification: {str(e)}")
            print(f"EXCEPTION in email notification: {str(e)}")
            return False
    
    def _get_status_color(self, status):
        """Get color for status badge based on status value"""
        status_colors = {
            'interested': "#28a745",  # Green
            'not_interested': "#dc3545",  # Red
            'pending': "#6f42c1",  # Purple
            'hold': "#ffc107",  # Yellow
            'processing': "#17a2b8",  # Sky blue
        }
        
        return status_colors.get(status.lower(), "#6c757d")  # Default gray
    
    def _get_loan_status_color(self, loan_status):
        """Get color for loan status badge based on loan status value"""
        loan_status_colors = {
            'approved': "#28a745",  # Green
            'processing': "#17a2b8",  # Blue
            'hold': "#ffc107",  # Orange
            'rejected': "#dc3545",  # Red
            'soon': "#6c757d",  # Gray
        }
        
        return loan_status_colors.get(loan_status.lower(), "#6c757d")  # Default gray
    
    def _create_tmis_email_template(self, client_data, admin_name, update_type):
        """Create HTML email template for TMIS users"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ line-height: 1.6; color: #333; }}
                .client-info {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .info-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .info-label {{ font-weight: bold; color: #555; }}
                .info-value {{ color: #333; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                .status-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Client {update_type.title()} Notification</h1>
                    <p>TMIS Business Guru</p>
                </div>
                
                <div class="content">
                    <p>Dear Team,</p>
                    
                    <p>A client has been <strong>{update_type}</strong> by <strong>{admin_name}</strong> in the TMIS Business Guru system.</p>
                    
                    <div class="client-info">
                        <h3 style="margin-top: 0; color: #333;">📋 Client Details</h3>
                        
                        <div class="info-row">
                            <span class="info-label">Legal Name:</span>
                            <span class="info-value">{client_data.get('legal_name', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Trade Name:</span>
                            <span class="info-value">{client_data.get('trade_name', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Registration Number:</span>
                            <span class="info-value">{client_data.get('registration_number', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Constitution Type:</span>
                            <span class="info-value">{client_data.get('constitution_type', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Mobile Number:</span>
                            <span class="info-value">{client_data.get('mobile_number', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Status:</span>
                            <span class="status-badge" style="background-color: {self._get_status_color(client_data.get('status', ''))};">{client_data.get('status', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Loan Status:</span>
                            <span class="status-badge" style="background-color: {self._get_loan_status_color(client_data.get('loan_status', 'soon'))};">{client_data.get('loan_status', 'soon').title()}</span>
                        </div>
                        
                        {f'''<div class="info-row">
                            <span class="info-label">User Email:</span>
                            <span class="info-value">{client_data.get('user_email', 'N/A')}</span>
                        </div>''' if client_data.get('user_email') else ''}
                        
                        {f'''<div class="info-row">
                            <span class="info-label">Company Email:</span>
                            <span class="info-value">{client_data.get('company_email', 'N/A')}</span>
                        </div>''' if client_data.get('company_email') else ''}
                    </div>
                    
                    <p><strong>Updated by:</strong> {admin_name}</p>
                    <p><strong>Updated on:</strong> {current_time}</p>
                    
                    <p>Please log in to the TMIS Business Guru system to view complete client details and take necessary actions.</p>
                    
                    <p>Best regards,<br>
                    <strong>TMIS Business Guru System</strong></p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from TMIS Business Guru system.</p>
                    <p>&copy; 2024 TMIS Business Guru. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _create_client_email_template(self, client_data, update_type):
        """Create HTML email template for client emails"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 30px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ line-height: 1.6; color: #333; }}
                .client-info {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .info-row {{ display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }}
                .info-label {{ font-weight: bold; color: #555; }}
                .info-value {{ color: #333; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666; font-size: 12px; }}
                .status-badge {{ padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 Your Business Application Status Update</h1>
                </div>
                
                <div class="content">
                    <p>Dear Client,</p>
                    
                    <p>Your business application has been <strong>{update_type}</strong>.</p>
                    
                    <div class="client-info">
                        <h3 style="margin-top: 0; color: #333;">📋 Application Details</h3>
                        
                        <div class="info-row">
                            <span class="info-label">Legal Name:</span>
                            <span class="info-value">{client_data.get('legal_name', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Trade Name:</span>
                            <span class="info-value">{client_data.get('trade_name', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Registration Number:</span>
                            <span class="info-value">{client_data.get('registration_number', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Constitution Type:</span>
                            <span class="info-value">{client_data.get('constitution_type', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Mobile Number:</span>
                            <span class="info-value">{client_data.get('mobile_number', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Status:</span>
                            <span class="status-badge" style="background-color: {self._get_status_color(client_data.get('status', ''))};">{client_data.get('status', 'N/A')}</span>
                        </div>
                        
                        <div class="info-row">
                            <span class="info-label">Loan Status:</span>
                            <span class="status-badge" style="background-color: {self._get_loan_status_color(client_data.get('loan_status', 'soon'))};">{client_data.get('loan_status', 'soon').title()}</span>
                        </div>
                        
                        {f'''<div class="info-row">
                            <span class="info-label">User Email:</span>
                            <span class="info-value">{client_data.get('user_email', 'N/A')}</span>
                        </div>''' if client_data.get('user_email') else ''}
                        
                        {f'''<div class="info-row">
                            <span class="info-label">Company Email:</span>
                            <span class="info-value">{client_data.get('company_email', 'N/A')}</span>
                        </div>''' if client_data.get('company_email') else ''}
                    </div>
                    
                    <p><strong>Updated on:</strong> {current_time}</p>
                    
                    <p>If you have any questions or concerns about your application, please reply to this email or contact our support team.</p>
                    
                    <p>Best regards,<br>
                    <strong>Business Application Team</strong></p>
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from the Business Application system.</p>
                    <p>&#169; 2024 Business Application. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _send_email(self, recipients, subject, html_body):
        """Send email using SMTP configuration"""
        try:
            print(f"Attempting to send email to: {recipients}")
            print(f"SMTP Email: {self.smtp_email}")
            print(f"SMTP Server: {self.smtp_server}:{self.smtp_port}")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.smtp_email  # Use SMTP_EMAIL as sender
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                print("SMTP connection established, logging in...")
                server.login(self.smtp_email, self.smtp_password)
                print("SMTP login successful, sending email...")
                server.send_message(msg)
                print(f"Email sent successfully to {len(recipients)} recipients")
            
            return True
            
        except Exception as e:
            self.logger.error(f"SMTP Error: {str(e)}")
            print(f"SMTP Error details: {str(e)}")
            return False

# Create global email service instance
email_service = EmailService()
