#!/usr/bin/env python
"""
Google Drive Initialization Script for Kodomo Shokudo Survey

This script creates a new Google Drive folder for storing uploaded photos
for the Kodomo Shokudo Survey application, and updates the .env file with
the folder ID.

Usage:
    python init_drive.py [--folder_name FOLDER_NAME] [--email EMAIL]

If email is provided, the script will share the folder with that email address.

Requirements:
    - Google API credentials must be set up
    - GOOGLE_SERVICE_ACCOUNT_FILE environment variable must be set
"""

import os
import sys
import argparse
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_service():
    """Create Google Drive API service"""
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    
    if not service_account_file:
        print("Error: GOOGLE_SERVICE_ACCOUNT_FILE environment variable not set")
        print("Please set this variable in your .env file")
        sys.exit(1)
    
    if not os.path.exists(service_account_file):
        print(f"Error: Service account file not found at {service_account_file}")
        print("Please check the path and make sure the file exists")
        sys.exit(1)
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating Google Drive service: {e}")
        sys.exit(1)

def create_folder(service, folder_name):
    """Create a new folder in Google Drive"""
    try:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=file_metadata,
            fields='id, webViewLink'
        ).execute()
        
        print(f"Created new folder with ID: {folder['id']}")
        print(f"Folder URL: {folder['webViewLink']}")
        
        return folder['id']
    except Exception as e:
        print(f"Error creating folder: {e}")
        sys.exit(1)

def share_folder(service, folder_id, email):
    """Share the folder with the specified email"""
    try:
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        service.permissions().create(
            fileId=folder_id,
            body=permission,
            fields='id',
            sendNotificationEmail=True
        ).execute()
        
        print(f"Folder shared with {email}")
    except Exception as e:
        print(f"Error sharing folder: {e}")
        # Continue execution even if sharing fails

def update_env_file(folder_id):
    """Update .env file with the folder ID"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"Warning: {env_file} not found. Creating new file.")
        with open(env_file, 'w') as f:
            f.write(f"GOOGLE_DRIVE_FOLDER_ID={folder_id}\n")
        return
    
    # Read existing .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check if GOOGLE_DRIVE_FOLDER_ID already exists
    folder_id_exists = False
    for i, line in enumerate(lines):
        if line.startswith('GOOGLE_DRIVE_FOLDER_ID='):
            lines[i] = f"GOOGLE_DRIVE_FOLDER_ID={folder_id}\n"
            folder_id_exists = True
            break
    
    # Add GOOGLE_DRIVE_FOLDER_ID if it doesn't exist
    if not folder_id_exists:
        lines.append(f"GOOGLE_DRIVE_FOLDER_ID={folder_id}\n")
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Updated {env_file} with GOOGLE_DRIVE_FOLDER_ID={folder_id}")

def get_service_account_email():
    """Get the service account email from the service account file"""
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    
    if not service_account_file or not os.path.exists(service_account_file):
        return None
    
    try:
        import json
        with open(service_account_file, 'r') as f:
            service_account_info = json.load(f)
        
        return service_account_info.get('client_email')
    except Exception as e:
        print(f"Error getting service account email: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Initialize Google Drive for Kodomo Shokudo Survey')
    parser.add_argument('--folder_name', default='Kodomo Shokudo Survey Photos', help='Name of the folder to create')
    parser.add_argument('--email', help='Email address to share the folder with')
    args = parser.parse_args()
    
    print("Initializing Google Drive for Kodomo Shokudo Survey...")
    
    # Create Google Drive API service
    service = create_service()
    
    # Create folder
    folder_id = create_folder(service, args.folder_name)
    
    # Share folder with service account
    service_account_email = get_service_account_email()
    if service_account_email:
        share_folder(service, folder_id, service_account_email)
    
    # Share folder with user if email is provided
    if args.email:
        share_folder(service, folder_id, args.email)
    
    # Update .env file
    update_env_file(folder_id)
    
    print("Initialization complete!")
    print(f"Folder ID: {folder_id}")
    print(f"Make sure to set this ID in your .env file as GOOGLE_DRIVE_FOLDER_ID={folder_id}")
    
    if args.email:
        print(f"The folder has been shared with {args.email}")
    else:
        print("Note: The folder is owned by the service account and not shared with anyone except the service account.")
        print("To share the folder, run the script again with the --email parameter:")
        print(f"  python init_drive.py --folder_id {folder_id} --email your.email@example.com")

if __name__ == '__main__':
    main()
