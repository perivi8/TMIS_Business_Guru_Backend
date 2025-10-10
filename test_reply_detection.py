import sys
import os

# Add the current directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the functions we need to test
from enquiry_routes import _is_reply_option, _get_reply_response

def test_reply_detection():
    """Test the reply option detection functionality"""
    print("Testing reply option detection...")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        "Get Loan",
        "get loan",
        "GET LOAN",
        " Get Loan ",
        "Check Eligibility",
        "check eligibility",
        "CHECK ELIGIBILITY",
        " Check Eligibility ",
        "More Details",
        "more details",
        "MORE DETAILS",
        " More Details ",
        "Invalid Option",
        "",
        None
    ]
    
    for test_case in test_cases:
        try:
            result = _is_reply_option(test_case)
            print(f"Input: {repr(test_case)} -> Is reply option: {result}")
            
            if result and test_case:
                response = _get_reply_response(test_case)
                print(f"  Response: {response[:50]}...")
        except Exception as e:
            print(f"Input: {repr(test_case)} -> Error: {e}")
        print()

if __name__ == "__main__":
    test_reply_detection()