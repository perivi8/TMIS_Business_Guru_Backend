from datetime import datetime
from bson import ObjectId

class User:
    def __init__(self, username, email, password, role='user'):
        self.username = username
        self.email = email
        self.password = password
        self.role = role
        self.created_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'role': self.role,
            'created_at': self.created_at
        }

class Client:
    def __init__(self, user_name, mobile_number, email, business_name, district, 
                 business_pan, ie_code, new_current_account, website, gateway,
                 transaction_done_by_client, required_loan_amount, bank_account,
                 staff_id, bank_type, gst_status, documents=None, business_nature=None, comments=None):
        self.user_name = user_name
        self.mobile_number = mobile_number
        self.email = email
        self.business_name = business_name
        self.district = district
        self.business_pan = business_pan
        self.ie_code = ie_code
        self.new_current_account = new_current_account
        self.website = website
        self.gateway = gateway
        self.transaction_done_by_client = transaction_done_by_client
        self.required_loan_amount = required_loan_amount
        self.bank_account = bank_account
        self.staff_id = staff_id
        self.bank_type = bank_type
        self.gst_status = gst_status
        self.business_nature = business_nature
        self.comments = comments
        self.documents = documents or {}
        self.status = 'pending'  # pending, interested, not_interested, hold
        self.feedback = ''
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'user_name': self.user_name,
            'mobile_number': self.mobile_number,
            'email': self.email,
            'business_name': self.business_name,
            'district': self.district,
            'business_pan': self.business_pan,
            'ie_code': self.ie_code,
            'new_current_account': self.new_current_account,
            'website': self.website,
            'gateway': self.gateway,
            'transaction_done_by_client': self.transaction_done_by_client,
            'required_loan_amount': self.required_loan_amount,
            'bank_account': self.bank_account,
            'staff_id': self.staff_id,
            'bank_type': self.bank_type,
            'gst_status': self.gst_status,
            'business_nature': self.business_nature,
            'comments': self.comments,
            'documents': self.documents,
            'status': self.status,
            'feedback': self.feedback,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }