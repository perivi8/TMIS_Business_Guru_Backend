#!/usr/bin/env python3
"""
Setup script to configure Gemini API key for TMIS Business Guru
"""

import os
import re
from dotenv import load_dotenv

def setup_gemini_api_key():
    """Interactive setup for Gemini API key"""
    print("🤖 TMIS Business Guru - Gemini AI Setup")
    print("=" * 50)
    
    # Load current .env file
    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"❌ .env file not found at {env_file}")
        return False
    
    # Read current .env content
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Check if GEMINI_API_KEY already exists
    current_key = None
    if 'GEMINI_API_KEY=' in env_content:
        match = re.search(r'GEMINI_API_KEY=(.+)', env_content)
        if match:
            current_key = match.group(1).strip()
    
    if current_key:
        print(f"📋 Current Gemini API Key: {current_key[:10]}...")
        replace = input("🔄 Do you want to replace it? (y/N): ").lower().strip()
        if replace != 'y':
            print("✅ Keeping current API key.")
            return True
    
    # Get new API key from user
    print("\n📝 To get your Gemini API key:")
    print("   1. Go to: https://makersuite.google.com/app/apikey")
    print("   2. Sign in with your Google account")
    print("   3. Click 'Create API Key'")
    print("   4. Copy the generated key")
    print()
    
    new_key = input("🔑 Enter your Gemini API key: ").strip()
    
    if not new_key:
        print("❌ No API key provided. Setup cancelled.")
        return False
    
    # Validate API key format (basic check)
    if not new_key.startswith('AIza') or len(new_key) < 30:
        print("⚠️ Warning: This doesn't look like a valid Gemini API key.")
        print("   Gemini API keys typically start with 'AIza' and are ~39 characters long.")
        confirm = input("🤔 Continue anyway? (y/N): ").lower().strip()
        if confirm != 'y':
            print("❌ Setup cancelled.")
            return False
    
    # Update .env file
    try:
        if current_key:
            # Replace existing key
            new_content = re.sub(
                r'GEMINI_API_KEY=.+',
                f'GEMINI_API_KEY={new_key}',
                env_content
            )
        else:
            # Add new key
            if not env_content.endswith('\n'):
                env_content += '\n'
            new_content = env_content + f'\n# Gemini AI Configuration\nGEMINI_API_KEY={new_key}\n'
        
        # Write updated content
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Gemini API key updated successfully!")
        print(f"📁 Updated file: {os.path.abspath(env_file)}")
        
        # Test the new key
        print("\n🧪 Testing the new API key...")
        test_result = test_gemini_connection(new_key)
        
        if test_result:
            print("🎉 Setup completed successfully! The AI integration is ready to use.")
        else:
            print("⚠️ Setup completed but API key test failed. Please verify your key.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def test_gemini_connection(api_key):
    """Test if the provided API key works"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test
        response = model.generate_content("Hello, respond with just 'OK' if you can read this.")
        
        if response and response.text:
            print(f"✅ API key test successful!")
            return True
        else:
            print("❌ API key test failed - no response")
            return False
            
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

if __name__ == "__main__":
    try:
        success = setup_gemini_api_key()
        if success:
            print("\n💡 Next steps:")
            print("   1. Restart your backend server")
            print("   2. Run: python test_gemini_integration.py")
            print("   3. Test the AI functionality in the web app")
        else:
            print("\n❌ Setup failed. Please try again or check the documentation.")
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
