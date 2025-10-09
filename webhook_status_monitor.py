#!/usr/bin/env python3
"""
Webhook Status Monitor - Shows real-time webhook notifications
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

# Create a simple in-memory store for recent webhook events
webhook_events = []
MAX_EVENTS = 50

webhook_monitor_bp = Blueprint('webhook_monitor', __name__)
logger = logging.getLogger(__name__)

def add_webhook_event(event_type, status, message, details=None):
    """Add a webhook event to the monitor"""
    global webhook_events
    
    event = {
        'id': len(webhook_events) + 1,
        'type': event_type,
        'status': status,  # success, warning, error, info
        'message': message,
        'details': details or {},
        'timestamp': datetime.utcnow().isoformat()
    }
    
    webhook_events.insert(0, event)  # Add to beginning
    
    # Keep only last MAX_EVENTS
    if len(webhook_events) > MAX_EVENTS:
        webhook_events = webhook_events[:MAX_EVENTS]
    
    logger.info(f"📊 Webhook event added: {status} - {message}")
    
    return event

@webhook_monitor_bp.route('/webhook-status', methods=['GET'])
def get_webhook_status():
    """Get recent webhook events and status"""
    return jsonify({
        'status': 'active',
        'message': 'Webhook monitoring active',
        'events': webhook_events[:10],  # Return last 10 events
        'total_events': len(webhook_events),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@webhook_monitor_bp.route('/webhook-status/clear', methods=['POST'])
def clear_webhook_events():
    """Clear webhook events history"""
    global webhook_events
    webhook_events = []
    
    return jsonify({
        'status': 'success',
        'message': 'Webhook events cleared',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# Function to be called from enquiry_routes.py
def notify_webhook_event(event_type, status, message, details=None):
    """Function to be called from other modules to add webhook events"""
    return add_webhook_event(event_type, status, message, details)
