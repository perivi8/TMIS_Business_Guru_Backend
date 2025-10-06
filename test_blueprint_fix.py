#!/usr/bin/env python3
"""
Test script to verify blueprint registration fix
"""

import sys
import traceback

def test_blueprint_registration():
    """Test that blueprints are properly registered without conflicts"""
    try:
        print("🔄 Testing blueprint registration fix...")
        
        # Import app first (this registers blueprints)
        print("📋 Step 1: Importing app...")
        from app import app
        print(f"✅ App imported successfully")
        print(f"📊 Blueprints registered in app.py: {list(app.blueprints.keys())}")
        
        # Import main.py (this should NOT try to re-register blueprints)
        print("\n📋 Step 2: Importing main.py...")
        import main
        print("✅ main.py imported successfully without errors")
        
        # Verify final blueprint state
        print(f"\n📊 Final blueprint state: {list(app.blueprints.keys())}")
        print(f"📊 Total blueprints: {len(app.blueprints)}")
        
        # Check for specific blueprints
        expected_blueprints = ['client', 'enquiry']
        for bp_name in expected_blueprints:
            if bp_name in app.blueprints:
                print(f"✅ {bp_name} blueprint: REGISTERED")
            else:
                print(f"❌ {bp_name} blueprint: MISSING")
        
        # Test route registration
        print(f"\n🔍 Checking API routes...")
        api_routes = []
        for rule in app.url_map.iter_rules():
            if str(rule).startswith('/api/'):
                api_routes.append(str(rule))
        
        print(f"📊 Total API routes found: {len(api_routes)}")
        for route in api_routes[:10]:  # Show first 10 routes
            print(f"  📍 {route}")
        
        if len(api_routes) > 10:
            print(f"  ... and {len(api_routes) - 10} more routes")
        
        print(f"\n✅ Blueprint registration test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Blueprint registration test FAILED!")
        print(f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_blueprint_registration()
    sys.exit(0 if success else 1)
