#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import sys
import os
import traceback

print("=" * 60)
print("Testing Backend Imports")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print("-" * 60)

# Test basic imports
print("\n1. Testing basic imports...")
try:
    from flask import Flask
    print("✅ Flask imported")
except Exception as e:
    print(f"❌ Flask import failed: {e}")

try:
    from pymongo import MongoClient
    print("✅ PyMongo imported")
except Exception as e:
    print(f"❌ PyMongo import failed: {e}")

try:
    import pandas
    print("✅ Pandas imported")
except Exception as e:
    print(f"❌ Pandas import failed: {e}")

try:
    import PyPDF2
    print("✅ PyPDF2 imported")
except Exception as e:
    print(f"❌ PyPDF2 import failed: {e}")

# Test app import
print("\n2. Testing app import...")
try:
    from app import app
    print("✅ app imported successfully")
except Exception as e:
    print(f"❌ app import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# Test document_processor import
print("\n3. Testing document_processor import...")
try:
    from document_processor import DocumentProcessor
    print("✅ DocumentProcessor imported successfully")
except Exception as e:
    print(f"❌ DocumentProcessor import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# Test email_service import
print("\n4. Testing email_service import...")
try:
    from email_service import email_service
    print("✅ email_service imported successfully")
except Exception as e:
    print(f"❌ email_service import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# Test client_routes import
print("\n5. Testing client_routes import...")
try:
    from client_routes import client_bp
    print("✅ client_bp imported successfully")
except Exception as e:
    print(f"❌ client_bp import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

# Test enquiry_routes import
print("\n6. Testing enquiry_routes import...")
try:
    from enquiry_routes import enquiry_bp
    print("✅ enquiry_bp imported successfully")
except Exception as e:
    print(f"❌ enquiry_bp import failed: {e}")
    print(f"Traceback: {traceback.format_exc()}")

print("\n" + "=" * 60)
print("Import test complete!")
print("=" * 60)
