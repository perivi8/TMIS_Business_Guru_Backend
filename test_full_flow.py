import sys
import os
import json

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions we need to test
from enquiry_routes import _is_reply_option, _get_reply_response

def test_full_flow():
    """Test the full flow from clicking a link to receiving a response"""
    print("Testing full flow...")
    print("=" * 50)
    
    # Simulate messages that would be sent when clicking the links
    test_messages = [
        "Get Loan",
        "Check Eligibility", 
        "More Details"
    ]
    
    for message in test_messages:
        print(f"Testing message: '{message}'")
        
        # Check if it's a reply option
        is_reply = _is_reply_option(message)
        print(f"  Is reply option: {is_reply}")
        
        if is_reply:
            # Get the response
            response = _get_reply_response(message)
            print(f"  Response: {response}")
        else:
            print(f"  Not a recognized reply option")
        
        print()

if __name__ == "__main__":
    test_full_flow()