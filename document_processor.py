import PyPDF2
import re
from datetime import datetime
import pandas as pd
import json

class DocumentProcessor:
    def __init__(self):
        pass
    
    def extract_gst_info(self, pdf_path):
        """Extract information from GST document"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # Extract business name (trade name)
            business_name_pattern = r'Trade Name[:\s]*([A-Za-z\s&.,]+)'
            business_name_match = re.search(business_name_pattern, text, re.IGNORECASE)
            business_name = business_name_match.group(1).strip() if business_name_match else ""
            
            # Extract district
            district_pattern = r'District[:\s]*([A-Za-z\s]+)'
            district_match = re.search(district_pattern, text, re.IGNORECASE)
            district = district_match.group(1).strip() if district_match else ""
            
            # Extract GST status
            gst_status_pattern = r'Status[:\s]*([A-Za-z\s]+)'
            gst_status_match = re.search(gst_status_pattern, text, re.IGNORECASE)
            gst_status = gst_status_match.group(1).strip() if gst_status_match else ""
            
            # Determine business type
            business_type = "Unknown"
            if "private limited" in text.lower():
                business_type = "Private Limited"
            elif "partnership" in text.lower():
                business_type = "Partnership"
            elif "proprietorship" in text.lower():
                business_type = "Proprietorship"
            
            return {
                'business_name': business_name,
                'district': district,
                'gst_status': gst_status,
                'business_type': business_type
            }
        except Exception as e:
            print(f"Error extracting GST info: {str(e)}")
            return {}
    
    def extract_msme_info(self, pdf_path):
        """Extract information from MSME/Udyam document"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # Extract district if not found in GST
            district_pattern = r'District[:\s]*([A-Za-z\s]+)'
            district_match = re.search(district_pattern, text, re.IGNORECASE)
            district = district_match.group(1).strip() if district_match else ""
            
            return {
                'district': district
            }
        except Exception as e:
            print(f"Error extracting MSME info: {str(e)}")
            return {}
    
    def extract_bank_statement_info(self, pdf_path):
        """Extract information from bank statement"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # Extract bank name
            bank_name_patterns = [
                r'(State Bank of India|SBI)',
                r'(HDFC Bank|HDFC)',
                r'(ICICI Bank|ICICI)',
                r'(Axis Bank|AXIS)',
                r'(Punjab National Bank|PNB)',
                r'(Bank of Baroda|BOB)',
                r'(Canara Bank)',
                r'(Union Bank)',
                r'(Indian Bank)',
                r'(Central Bank)'
            ]
            
            bank_name = "Unknown"
            for pattern in bank_name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    bank_name = match.group(1)
                    break
            
            # Extract credit transactions
            credit_pattern = r'(\d+\.?\d*)\s*CR'
            credit_matches = re.findall(credit_pattern, text)
            credit_transactions = [float(amount) for amount in credit_matches if float(amount) > 1000]
            
            # Calculate total credits and average
            total_credits = sum(credit_transactions)
            avg_monthly_credits = total_credits / 12 if len(credit_transactions) > 0 else 0
            
            # Analyze statement period (assuming 12 months)
            months_analyzed = 12
            
            return {
                'bank_name': bank_name,
                'total_credits': total_credits,
                'avg_monthly_credits': avg_monthly_credits,
                'months_analyzed': months_analyzed,
                'credit_transactions': len(credit_transactions)
            }
        except Exception as e:
            print(f"Error extracting bank statement info: {str(e)}")
            return {}
    
    def process_all_documents(self, documents):
        """Process all uploaded documents and extract relevant information"""
        extracted_data = {}
        
        if 'gst_document' in documents:
            gst_info = self.extract_gst_info(documents['gst_document'])
            extracted_data.update(gst_info)
        
        if 'msme_document' in documents:
            msme_info = self.extract_msme_info(documents['msme_document'])
            # Only update district if not found in GST
            if 'district' not in extracted_data or not extracted_data['district']:
                extracted_data.update(msme_info)
        
        # Process multiple bank statements (bank_statement_0, bank_statement_1, etc.)
        bank_statement_keys = [key for key in documents.keys() if key.startswith('bank_statement_')]
        if bank_statement_keys:
            # Process the first bank statement for extracting bank info
            first_bank_statement = bank_statement_keys[0]
            bank_info = self.extract_bank_statement_info(documents[first_bank_statement])
            extracted_data.update(bank_info)
        
        # Legacy support for single bank_statement field
        if 'bank_statement' in documents:
            bank_info = self.extract_bank_statement_info(documents['bank_statement'])
            extracted_data.update(bank_info)
        
        return extracted_data
