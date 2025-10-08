import os
import sys

# Set environment variables to mimic production
os.environ['FLASK_ENV'] = 'production'
os.environ['MONGODB_URI'] = 'mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0'
os.environ['JWT_SECRET_KEY'] = 'tmis-business-guru-secret-key-2024'

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== Testing Full App Startup ===")

try:
    # Import app similar to how it's done in main.py
    print("🔄 Importing app...")
    from app import app
    print("✅ App imported successfully")
    
    # Check registered blueprints
    print(f"📋 Registered blueprints: {list(app.blueprints.keys())}")
    
    # Check if webhook route is registered
    webhook_routes = []
    for rule in app.url_map.iter_rules():
        if 'webhook' in str(rule).lower():
            webhook_routes.append(str(rule))
    
    if webhook_routes:
        print("✅ Webhook routes found:")
        for route in webhook_routes:
            print(f"  {route}")
    else:
        print("❌ No webhook routes found")
        
    # Check all API routes
    print("\n=== All API Routes ===")
    api_routes = []
    for rule in app.url_map.iter_rules():
        if str(rule).startswith('/api/'):
            api_routes.append(str(rule))
    
    for route in sorted(api_routes):
        print(f"  {route}")
        
except Exception as e:
    print(f"❌ Error during app startup: {e}")
    import traceback
    traceback.print_exc()