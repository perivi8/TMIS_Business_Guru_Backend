import urllib.parse

def test_clickable_links():
    """Test the clickable links functionality"""
    print("Testing clickable links...")
    print("=" * 50)
    
    # Base WhatsApp URL
    base_url = "https://wa.me/918106811285"
    
    # Test messages
    messages = [
        "Get Loan",
        "Check Eligibility", 
        "More Details"
    ]
    
    for message in messages:
        # URL encode the message
        encoded_message = urllib.parse.quote(message)
        full_url = f"{base_url}?text={encoded_message}"
        
        print(f"Option: {message}")
        print(f"URL: {full_url}")
        print()

if __name__ == "__main__":
    test_clickable_links()