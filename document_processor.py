import PyPDF2
import re
from datetime import datetime
import pandas as pd
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
from PIL import Image
import pytesseract

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Initialize Gemini AI
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_ai = True
                logger.info("✅ Gemini AI initialized for document processing")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Gemini AI: {e}. Falling back to regex extraction.")
                self.use_ai = False
        else:
            logger.warning("⚠️ GEMINI_API_KEY not found. Using regex extraction.")
            self.use_ai = False
    
    def extract_gst_info(self, file_path):
        """Extract information from GST document (PDF or image) using AI or fallback to regex"""
        try:
            text = self._extract_text_from_file(file_path)
            
            if self.use_ai and text.strip():
                return self._extract_gst_info_with_ai(text)
            else:
                return self._extract_gst_info_with_regex(text)
                
        except Exception as e:
            logger.error(f"Error extracting GST info: {str(e)}")
            return {}
    
    def _extract_text_from_file(self, file_path):
        """Extract text from PDF or image file"""
        try:
            # Get file extension
            _, ext = os.path.splitext(file_path.lower())
            
            if ext == '.pdf':
                # Extract text from PDF
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                # Extract text from image using OCR
                try:
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image)
                    return text
                except Exception as ocr_error:
                    logger.warning(f"⚠️ OCR failed: {ocr_error}. Trying without OCR.")
                    return ""
            else:
                logger.warning(f"⚠️ Unsupported file format: {ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            return ""
    
    def _extract_gst_info_with_ai(self, text):
        """Extract GST information using Gemini AI"""
        try:
            prompt = f"""
            Analyze the following GST document text and extract the required information. 
            Return the data in JSON format with the following fields:
            - registration_number: GST registration number (15 characters)
            - legal_name: Legal name of business (from "Legal Name of Business" field)
            - trade_name: Trade name or business name (from "Trade Name" field)
            - address: Complete business address (specifically from "Principal Place of Business" field)
            - state: State name (from "State Name" field)
            - district: District name (from "District" field)
            - pincode: 6-digit pincode (from "Pin Code" field)
            - gst_status: GST registration status (Active, Inactive, Cancelled, etc.) (from "Status" field)
            - business_type: Type of business (Proprietorship, Partnership, Private Limited, etc.)
            
            Document text:
            {text[:4000]}  # Limit text to avoid token limits
            
            Return only valid JSON without any additional text or explanation.
            """
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Clean the response to extract JSON
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                if response_text.startswith('```'):
                    response_text = response_text[3:]
                
                response_text = response_text.strip()
                
                try:
                    extracted_data = json.loads(response_text)
                    logger.info("✅ Successfully extracted GST data using Gemini AI")
                    return extracted_data
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse AI response as JSON: {e}. Falling back to regex.")
                    return self._extract_gst_info_with_regex(text)
            else:
                logger.warning("⚠️ No response from Gemini AI. Falling back to regex.")
                return self._extract_gst_info_with_regex(text)
                
        except Exception as e:
            logger.error(f"❌ Error using Gemini AI for GST extraction: {e}. Falling back to regex.")
            return self._extract_gst_info_with_regex(text)
    
    def _extract_gst_info_with_regex(self, text):
        """Extract GST information using regex patterns (fallback method)"""
        try:
            # Extract GST number (registration number)
            gst_number_pattern = r'GSTIN\s*[:\-]?\s*([0-9A-Z]{15})'
            gst_number_match = re.search(gst_number_pattern, text, re.IGNORECASE)
            gst_number = gst_number_match.group(1).strip() if gst_number_match else ""
            
            # Extract legal name - more flexible pattern
            legal_name_pattern = r'Legal Name of Business\s*[:\-]?\s*([^\n\r]+)'
            legal_name_match = re.search(legal_name_pattern, text, re.IGNORECASE)
            legal_name = legal_name_match.group(1).strip() if legal_name_match else ""
            
            # Extract trade name (business name) - more flexible pattern
            trade_name_pattern = r'Trade Name\s*[:\-]?\s*([^\n\r]+)'
            trade_name_match = re.search(trade_name_pattern, text, re.IGNORECASE)
            trade_name = trade_name_match.group(1).strip() if trade_name_match else ""
            
            # Extract address - specifically look for "Principal Place of Business"
            address_pattern = r'Principal Place of Business\s*[:\-]?\s*([^\n\r]+)'
            address_match = re.search(address_pattern, text, re.IGNORECASE)
            address = address_match.group(1).strip() if address_match else ""
            
            # If Principal Place of Business not found, try general address pattern
            if not address:
                address_pattern = r'Address\s*[:\-]?\s*([^\n\r]+)'
                address_match = re.search(address_pattern, text, re.IGNORECASE)
                address = address_match.group(1).strip() if address_match else ""
            
            # Extract state
            state_pattern = r'State Name\s*[:\-]?\s*([^\n\r]+)'
            state_match = re.search(state_pattern, text, re.IGNORECASE)
            state = state_match.group(1).strip() if state_match else ""
            
            # Extract district
            district_pattern = r'District\s*[:\-]?\s*([^\n\r]+)'
            district_match = re.search(district_pattern, text, re.IGNORECASE)
            district = district_match.group(1).strip() if district_match else ""
            
            # Extract pincode
            pincode_pattern = r'Pin Code\s*[:\-]?\s*(\d{6})'
            pincode_match = re.search(pincode_pattern, text, re.IGNORECASE)
            pincode = pincode_match.group(1).strip() if pincode_match else ""
            
            # Extract GST status
            gst_status_pattern = r'Status\s*[:\-]?\s*([^\n\r]+)'
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
            
            logger.info("✅ Extracted GST data using regex patterns")
            return {
                'registration_number': gst_number,
                'legal_name': legal_name,
                'trade_name': trade_name,
                'address': address,
                'state': state,
                'district': district,
                'pincode': pincode,
                'gst_status': gst_status,
                'business_type': business_type
            }
        except Exception as e:
            logger.error(f"Error in regex extraction: {str(e)}")
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
