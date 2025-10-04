#!/usr/bin/env python3
"""
GreenAPI Only Service - No Facebook API needed!
Send WhatsApp messages to ANY number without OTP verification
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

class GreenAPIOnlyService:
    """Pure GreenAPI service - No Facebook API dependency"""
    
    def __init__(self):
        self.instance_id = os.getenv('GREENAPI_INSTANCE_ID')
        self.token = os.getenv('GREENAPI_TOKEN')
        self.base_url = os.getenv('GREENAPI_BASE_URL')
        
        if self.instance_id and self.token:
            if not self.base_url:
                self.base_url = f"https://{self.instance_id}.api.greenapi.com"
            
            self.api_available = True
            logger.info(f"🌿 GreenAPI Only Service initialized")
            logger.info(f"📱 Instance ID: {self.instance_id}")
            logger.info(f"🌐 Base URL: {self.base_url}")
            logger.info(f"✅ NO FACEBOOK API NEEDED!")
            logger.info(f"🚀 Send to ANY number without OTP!")
        else:
            self.api_available = False
            logger.error("❌ GreenAPI credentials missing in .env file")
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send WhatsApp message to ANY number (no OTP required)
        
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
            
            logger.info(f"🌿 GreenAPI - Sending to {formatted_number}")
            logger.info(f"✅ NO OTP REQUIRED!")
            logger.info(f"🚀 NO FACEBOOK API NEEDED!")
            
            # GreenAPI endpoint
            url = f"{self.base_url}/waInstance{self.instance_id}/sendMessage/{self.token}"
            
            data = {
                "chatId": formatted_number,
                "message": message
            }
            
            logger.info(f"📤 URL: {url}")
            logger.info(f"📤 Payload: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, timeout=30)
            
            logger.info(f"📥 Status Code: {response.status_code}")
            logger.info(f"📥 Response Text: {response.text}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"📥 Response JSON: {json.dumps(response_data, indent=2)}")
                    
                    if response_data.get('idMessage'):
                        logger.info(f"✅ SUCCESS! Message sent to {formatted_number}")
                        return {
                            'success': True,
                            'message_id': response_data.get('idMessage'),
                            'service': 'GreenAPI Only',
                            'no_otp_required': True,
                            'no_facebook_needed': True,
                            'response': response_data
                        }
                    else:
                        logger.warning(f"⚠️ No message ID in response")
                        return {
                            'success': False,
                            'error': 'No message ID returned',
                            'service': 'GreenAPI Only',
                            'response': response_data
                        }
                except json.JSONDecodeError:
                    logger.error(f"❌ Invalid JSON response: {response.text}")
                    return {
                        'success': False,
                        'error': f'Invalid JSON response: {response.text}',
                        'service': 'GreenAPI Only'
                    }
            else:
                logger.error(f"❌ HTTP Error: {response.status_code}")
                logger.error(f"❌ Response: {response.text}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'service': 'GreenAPI Only',
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error: {str(e)}")
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'service': 'GreenAPI Only',
                'solution': 'Check internet connection and GreenAPI URL'
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'service': 'GreenAPI Only'
            }
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number for GreenAPI"""
        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone_number))
        
        # If number is 10 digits, assume it's Indian number and add country code
        if len(clean_number) == 10:
            clean_number = '91' + clean_number
        
        # GreenAPI expects format: 919876543210@c.us
        return f"{clean_number}@c.us"
    
    def check_status(self) -> Dict[str, Any]:
        """Check GreenAPI connection status"""
        if not self.api_available:
            return {
                'connected': False,
                'error': 'GreenAPI credentials not configured'
            }
        
        try:
            url = f"{self.base_url}/waInstance{self.instance_id}/getStateInstance/{self.token}"
            logger.info(f"📡 Checking status: {url}")
            
            response = requests.get(url, timeout=10)
            logger.info(f"📡 Status response: {response.status_code}")
            logger.info(f"📡 Status text: {response.text}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    state = response_data.get('stateInstance', 'unknown')
                    
                    return {
                        'connected': state == 'authorized',
                        'state': state,
                        'status': response_data,
                        'service': 'GreenAPI Only',
                        'no_facebook_needed': True
                    }
                except json.JSONDecodeError:
                    return {
                        'connected': False,
                        'error': f'Invalid JSON response: {response.text}',
                        'service': 'GreenAPI Only'
                    }
            else:
                return {
                    'connected': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'service': 'GreenAPI Only'
                }
                
        except Exception as e:
            return {
                'connected': False,
                'error': f'Status check error: {str(e)}',
                'service': 'GreenAPI Only'
            }
    
    def test_multiple_numbers(self, numbers: list) -> Dict[str, Any]:
        """Test sending messages to multiple numbers"""
        results = {}
        
        logger.info(f"🧪 Testing GreenAPI with {len(numbers)} numbers...")
        logger.info(f"✅ NO OTP required for ANY number!")
        logger.info(f"🚀 NO Facebook API needed!")
        
        for number in numbers:
            logger.info(f"\n📱 Testing {number}...")
            result = self.send_message(
                number, 
                f"🎉 GreenAPI Success! Message sent to {number} without OTP or Facebook API!"
            )
            results[number] = result
        
        return results

# Create global instance
try:
    greenapi_only_service = GreenAPIOnlyService()
    logger.info("✅ GreenAPI Only Service ready")
except Exception as e:
    logger.error(f"❌ Failed to initialize GreenAPI Only Service: {e}")
    greenapi_only_service = None

if __name__ == "__main__":
    """Test the GreenAPI only service"""
    if greenapi_only_service and greenapi_only_service.api_available:
        print("🌿 GreenAPI Only Service Test")
        print("=" * 50)
        print("✅ NO Facebook API needed!")
        print("✅ NO OTP required for customers!")
        print("✅ Send to ANY number worldwide!")
        
        # Check status first
        status = greenapi_only_service.check_status()
        print(f"\n📡 Connection Status:")
        print(f"   Connected: {'✅ Yes' if status.get('connected') else '❌ No'}")
        print(f"   State: {status.get('state', 'unknown')}")
        
        if status.get('connected'):
            test_numbers = [
                '918106811285',  # Your number
                '917010905730',  # Test number (should work without OTP!)
                '919876543210',  # Random test (should work without OTP!)
            ]
            
            print(f"\n🧪 Testing with numbers that FAILED Facebook API...")
            results = greenapi_only_service.test_multiple_numbers(test_numbers)
            
            print(f"\n📊 GREENAPI ONLY RESULTS:")
            successful = 0
            for number, result in results.items():
                if result['success']:
                    successful += 1
                    print(f"✅ {number}: SUCCESS (No OTP required!)")
                    print(f"   Message ID: {result.get('message_id', 'N/A')}")
                else:
                    print(f"❌ {number}: FAILED")
                    print(f"   Error: {result.get('error', 'Unknown')}")
            
            print(f"\n🎯 SUMMARY:")
            print(f"   Success Rate: {successful}/{len(test_numbers)} ({successful/len(test_numbers)*100:.1f}%)")
            print(f"   Facebook API: NOT NEEDED ✅")
            print(f"   OTP Required: NEVER ✅")
            
            if successful > 0:
                print(f"\n🎉 SUCCESS! GreenAPI can replace Facebook API!")
                print(f"✅ You can remove all Facebook API configuration")
                print(f"✅ Send to unlimited numbers without OTP")
        else:
            print(f"\n❌ GreenAPI not connected")
            print(f"   Error: {status.get('error', 'Unknown')}")
            print(f"\n🔧 Troubleshooting:")
            print(f"   1. Check internet connection")
            print(f"   2. Verify GreenAPI credentials")
            print(f"   3. Ensure WhatsApp is connected in GreenAPI dashboard")
    else:
        print("❌ GreenAPI Only Service not available")
        print("\n🔧 Configuration needed:")
        print("   GREENAPI_INSTANCE_ID=7105335459")
        print("   GREENAPI_TOKEN=3a0876a6822049bc...")
