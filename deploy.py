#!/usr/bin/env python3
"""
Deployment script for TMIS Business Guru Backend
This script helps prepare and deploy the backend to Render
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_files():
    """Check if all required files exist"""
    print("\n🔍 Checking required files...")
    
    required_files = [
        'main.py',
        'app.py', 
        'client_routes.py',
        'enquiry_routes.py',
        'requirements.txt',
        'Procfile',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_imports():
    """Test if all Python imports work"""
    print("\n🔍 Testing Python imports...")
    
    tests = [
        ("import main", "main.py"),
        ("from client_routes import client_bp", "client_routes.py"),
        ("from enquiry_routes import enquiry_bp", "enquiry_routes.py"),
        ("from app import app", "app.py")
    ]
    
    all_passed = True
    for test_cmd, description in tests:
        try:
            subprocess.run([sys.executable, "-c", test_cmd], check=True, capture_output=True)
            print(f"✅ {description} imports successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} import failed: {e.stderr.decode()}")
            all_passed = False
    
    return all_passed

def show_deployment_steps():
    """Show manual deployment steps"""
    print("\n" + "="*60)
    print("🚀 DEPLOYMENT STEPS")
    print("="*60)
    print("\n1. Commit your changes:")
    print("   git add .")
    print("   git commit -m 'Fix cloudinary import and blueprint registration'")
    print("   git push")
    
    print("\n2. Render will automatically redeploy when you push to the connected repository")
    
    print("\n3. Monitor deployment logs in Render dashboard:")
    print("   https://dashboard.render.com/")
    
    print("\n4. Test endpoints after deployment:")
    print("   https://tmis-business-guru-backend.onrender.com/")
    print("   https://tmis-business-guru-backend.onrender.com/api/health")
    print("   https://tmis-business-guru-backend.onrender.com/api/debug/database")
    
    print("\n5. Test client endpoint (requires JWT token):")
    print("   https://tmis-business-guru-backend.onrender.com/api/clients")

def main():
    """Main deployment preparation function"""
    print("🚀 TMIS Business Guru Backend Deployment Preparation")
    print("="*60)
    
    # Check current directory
    if not os.path.exists('main.py'):
        print("❌ Please run this script from the backend directory")
        return 1
    
    # Check files
    if not check_files():
        print("\n❌ Missing required files. Please ensure all files are present.")
        return 1
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please fix import errors before deployment.")
        return 1
    
    print("\n✅ All checks passed! Backend is ready for deployment.")
    
    # Show deployment steps
    show_deployment_steps()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
