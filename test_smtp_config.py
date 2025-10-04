#!/usr/bin/env python3
"""
Test SMTP Configuration for TMIS Business Guru
This script tests if the SMTP settings in .env file are working correctly
"""

import os
import smtplib
import email.mime.text
import email.mime.multipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_smtp_connection():
    """Test SMTP connection and authentication"""
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        print("🔧 SMTP Configuration Test")
        print("=" * 40)
        print(f"📧 SMTP Server: {smtp_server}")
        print(f"🔌 SMTP Port: {smtp_port}")
        print(f"👤 Email: {smtp_email}")
        print(f"🔑 Password: {'*' * len(smtp_password) if smtp_password else 'Not set'}")
        print()
        
        # Check if all required configuration is available
        if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
            print("❌ Missing SMTP configuration in .env file")
            missing = []
            if not smtp_server: missing.append("SMTP_SERVER")
            if not smtp_port: missing.append("SMTP_PORT")
            if not smtp_email: missing.append("SMTP_EMAIL")
            if not smtp_password: missing.append("SMTP_PASSWORD")
            print(f"Missing: {', '.join(missing)}")
            return False
        
        # Convert port to integer
        try:
            smtp_port = int(smtp_port)
        except (ValueError, TypeError):
            print("❌ Invalid SMTP port")
            return False
        
        print("🔄 Testing SMTP connection...")
        
        # Test connection
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("✅ Connected to SMTP server")
        
        # Start TLS
        server.starttls()
        print("✅ TLS encryption enabled")
        
        # Test authentication
        server.login(smtp_email, smtp_password)
        print("✅ SMTP authentication successful")
        
        # Close connection
        server.quit()
        print("✅ Connection closed properly")
        
        print()
        print("🎉 SMTP configuration is working correctly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {str(e)}")
        print("💡 Check your email and app password in .env file")
        print("💡 For Gmail, make sure you're using an App Password, not your regular password")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def send_test_email(to_email):
    """Send a test email"""
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        print(f"📤 Sending test email to: {to_email}")
        
        # Create message
        msg = email.mime.multipart.MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = "SMTP Test - TMIS Business Guru"
        
        body = """
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>Congratulations! Your SMTP configuration is working correctly.</p>
            <p>This test email was sent from the TMIS Business Guru system.</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>SMTP Server: {}</li>
                <li>SMTP Port: {}</li>
                <li>From Email: {}</li>
            </ul>
            <p>You can now use the forgot password feature!</p>
        </body>
        </html>
        """.format(smtp_server, smtp_port, smtp_email)
        
        msg.attach(email.mime.text.MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        
        text = msg.as_string()
        server.sendmail(smtp_email, to_email, text)
        server.quit()
        
        print(f"✅ Test email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting SMTP Configuration Test")
    print()
    
    # Test connection
    connection_ok = test_smtp_connection()
    
    if connection_ok:
        print()
        # Ask if user wants to send test email
        test_email = input("Enter email address to send test email (or press Enter to skip): ").strip()
        
        if test_email:
            print()
            send_test_email(test_email)
        else:
            print("⏭️  Skipping test email")
    
    print()
    print("✅ SMTP test completed!")
