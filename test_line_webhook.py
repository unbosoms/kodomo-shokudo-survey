#!/usr/bin/env python
"""
LINE Webhook Test Script for Kodomo Shokudo Survey

This script allows you to test the LINE webhook functionality locally by
simulating a webhook event from LINE. It sends a test message to the webhook
endpoint of your local Flask application.

Usage:
    python test_line_webhook.py [--message MESSAGE] [--user_id USER_ID]

Requirements:
    - Flask application must be running locally
    - LINE API credentials must be set up
"""

import os
import sys
import argparse
import json
import base64
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_signature(body, channel_secret):
    """Create a signature for the webhook event"""
    hash = hmac.new(channel_secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(hash).decode('utf-8')
    return signature

def create_text_message_event(user_id, message):
    """Create a text message event"""
    event = {
        "destination": "xxxxxxxxxx",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "12345678901234",
                    "text": message
                },
                "timestamp": 1625665242211,
                "source": {
                    "type": "user",
                    "userId": user_id
                },
                "replyToken": "test_reply_token",
                "mode": "active"
            }
        ]
    }
    return json.dumps(event)

def send_webhook_event(webhook_url, body, signature):
    """Send a webhook event to the webhook URL"""
    headers = {
        'Content-Type': 'application/json',
        'X-Line-Signature': signature
    }
    
    response = requests.post(webhook_url, headers=headers, data=body)
    
    return response

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test LINE webhook for Kodomo Shokudo Survey')
    parser.add_argument('--message', default='アンケート', help='Message text to send')
    parser.add_argument('--user_id', default='test_user_id', help='User ID to use')
    parser.add_argument('--webhook_url', default='http://localhost:5000/webhook', help='Webhook URL')
    args = parser.parse_args()
    
    # Get LINE channel secret
    channel_secret = os.getenv('LINE_CHANNEL_SECRET')
    if not channel_secret:
        print("Error: LINE_CHANNEL_SECRET environment variable not set")
        print("Please set this variable in your .env file")
        sys.exit(1)
    
    print("Testing LINE webhook for Kodomo Shokudo Survey...")
    print(f"Message: {args.message}")
    print(f"User ID: {args.user_id}")
    print(f"Webhook URL: {args.webhook_url}")
    
    # Create webhook event
    body = create_text_message_event(args.user_id, args.message)
    signature = create_signature(body, channel_secret)
    
    # Send webhook event
    try:
        response = send_webhook_event(args.webhook_url, body, signature)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("Webhook test successful!")
        else:
            print("Webhook test failed!")
    except Exception as e:
        print(f"Error sending webhook event: {e}")
        print("Make sure your Flask application is running locally.")
        sys.exit(1)

if __name__ == '__main__':
    main()
