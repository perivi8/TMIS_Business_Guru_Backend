#!/usr/bin/env python3
"""
Script to switch back to the full application
Run this after minimal app is working
"""

import os

def switch_to_full_app():
    """Switch Procfile back to main app"""
    procfile_content = "web: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:app\n"
    
    with open('Procfile', 'w') as f:
        f.write(procfile_content)
    
    print("✅ Procfile updated to use main:app")
    print("🚀 Now commit and push to deploy full application:")
    print("   git add Procfile")
    print("   git commit -m 'Switch back to full application'")
    print("   git push")

if __name__ == "__main__":
    switch_to_full_app()
