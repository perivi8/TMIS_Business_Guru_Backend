#!/bin/bash

# Production startup script for Render deployment
echo "🚀 Starting TMIS Business Guru Backend on Render..."

# Print environment info
echo "Environment: $FLASK_ENV"
echo "Port: $PORT"

# Check if MongoDB URI is set
if [ -z "$MONGODB_URI" ]; then
    echo "❌ ERROR: MONGODB_URI environment variable is not set!"
    echo "Please set it in your Render dashboard:"
    echo "MONGODB_URI=mongodb+srv://perivihk_db_user:perivihk_db_user@cluster0.5kqbeaz.mongodb.net/tmis_business_guru?retryWrites=true&w=majority&appName=Cluster0"
    exit 1
fi

echo "✅ MongoDB URI is set"
echo "✅ Starting TMIS Business Guru Backend with SocketIO support..."

# Start the application with SocketIO support
exec python start_server.py