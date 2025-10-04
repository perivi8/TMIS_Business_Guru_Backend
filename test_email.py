import os
from dotenv import load_dotenv
import smtplib
import email.mime.text
import email.mime.multipart

# Load environment variables
load_dotenv()

def test_email_config():
    """Test email configuration"""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP Email: {smtp_email}")
    print(f"SMTP Password: {'*' * len(smtp_password) if smtp_password else 'None'}")
    
    if not all([smtp_server, smtp_port, smtp_email, smtp_password]):
        print("❌ Missing SMTP configuration")
        return False
    
    try:
        # Test connection
        print("Testing SMTP connection...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.quit()
        print("✅ SMTP connection successful!")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False

if __name__ == "__main__":
    test_email_config()
