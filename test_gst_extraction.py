#!/usr/bin/env python3
"""
Test script for GST document extraction using direct AI analysis
"""

import os
import sys
from document_processor import DocumentProcessor

def test_gst_extraction():
    """Test GST document extraction with a sample document"""
    # Initialize the document processor
    processor = DocumentProcessor()
    
    # Check if AI is available
    if processor.use_ai:
        print("✅ Gemini AI is available for document processing")
    else:
        print("⚠️ Gemini AI is not available, using fallback methods")
        return
    
    # Look for sample GST documents in the current directory
    sample_files = []
    for file in os.listdir('.'):
        if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            sample_files.append(file)
    
    if not sample_files:
        print("⚠️ No sample GST documents found in current directory")
        print("Please add a GST document (PDF, JPG, JPEG, PNG) to test the extraction")
        return
    
    print(f"📄 Found {len(sample_files)} sample document(s):")
    for file in sample_files:
        print(f"  - {file}")
    
    # Test extraction on the first document
    test_file = sample_files[0]
    print(f"\n🔍 Testing extraction on: {test_file}")
    
    try:
        extracted_data = processor.extract_gst_info(test_file)
        print("\n📊 Extracted Data:")
        for key, value in extracted_data.items():
            print(f"  {key}: {value}")
        
        # Check if we got meaningful data
        if extracted_data:
            non_empty_fields = sum(1 for v in extracted_data.values() if v)
            print(f"\n✅ Successfully extracted {non_empty_fields} fields from the document")
        else:
            print("\n❌ No data was extracted from the document")
            
    except Exception as e:
        print(f"\n❌ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gst_extraction()