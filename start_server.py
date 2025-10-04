#!/usr/bin/env python3
"""
Startup script for TMIS Business Guru Backend
This script provides an alternative way to start the application with proper SocketIO support
"""

import os
import sys

def main():
    """Main entry point for the application"""
    # Set default environment variables if not present
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'production'
    
    if 'PORT' not in os.environ:
        os.environ['PORT'] = '5000'
    
    print(f"🚀 Starting TMIS Business Guru Backend...")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Port: {os.environ.get('PORT', '5000')}")
    
    # Import and run the main application
    try:
        from app import app, socketio
        port = int(os.environ.get('PORT', 5000))
        
        if os.environ.get('FLASK_ENV') == 'production':
            socketio.run(app, host='0.0.0.0', port=port, debug=False, log_output=False)
        else:
            socketio.run(app, host='0.0.0.0', port=port, debug=True)
            
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()