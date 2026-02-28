#!/usr/bin/env python
"""
Google Sheets Initialization Script for Kodomo Shokudo Survey

This script creates a new Google Sheets spreadsheet with the required structure
for the Kodomo Shokudo Survey application, or updates an existing spreadsheet
to match the required structure.

Usage:
    python init_spreadsheet.py [--spreadsheet_id SPREADSHEET_ID] [--email EMAIL]

If spreadsheet_id is provided, the script will update the existing spreadsheet.
Otherwise, it will create a new spreadsheet.

If email is provided, the script will share the spreadsheet with that email address.

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

REQUIRED_SHEETS = ['data', 'master_shokudo', 'master_user', 'master_quadrant', 'master_color']

def create_credentials():
    """Create Google API credentials with both Sheets and Drive scopes"""
    # spreadsheets.create はDriveにファイルを作成するため drive スコープも必要
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
    ]

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
        return service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=scopes
        )
    except Exception as e:
        print(f"Error loading service account credentials: {e}")
        sys.exit(1)


def create_service(scopes=None):
    """Create Google Sheets API service"""
    credentials = create_credentials()
    try:
        return build('sheets', 'v4', credentials=credentials)
    except Exception as e:
        print(f"Error creating Google Sheets API service: {e}")
        sys.exit(1)


def create_drive_service():
    """Create Google Drive API service"""
    credentials = create_credentials()
    try:
        return build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"Error creating Google Drive API service: {e}")
        sys.exit(1)

def share_spreadsheet(spreadsheet_id, email):
    """Share the spreadsheet with the specified email"""
    if not email:
        print("No email provided, skipping sharing")
        return

    try:
        drive_service = create_drive_service()

        # Create permission
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': email
        }
        
        # Share the spreadsheet
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            fields='id',
            sendNotificationEmail=True
        ).execute()
        
        print(f"Spreadsheet shared with {email}")
    except Exception as e:
        print(f"Error sharing spreadsheet: {e}")
        print("You may need to manually share the spreadsheet.")

def create_spreadsheet(service, email=None, title="こども食堂アンケート"):
    """Create a new spreadsheet via Drive API, then add sheets via Sheets API"""
    try:
        # Drive API でスプレッドシートファイルを作成
        # (spreadsheets.create は組織ポリシー等で403になる場合があるため Drive API を使用)
        drive_service = create_drive_service()
        file = drive_service.files().create(
            body={
                'name': title,
                'mimeType': 'application/vnd.google-apps.spreadsheet',
            },
            fields='id,webViewLink'
        ).execute()

        spreadsheet_id = file['id']
        print(f"Created new spreadsheet with ID: {spreadsheet_id}")
        print(f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        # Sheets API でシートを追加・リネーム
        # (Drive API 作成時は "Sheet1" という名前のシートが1枚できる)
        sheet_names = ['data', 'master_shokudo', 'master_user', 'master_quadrant', 'master_color']
        requests = [
            # 既存の Sheet1 を最初のシート名にリネーム
            {
                'updateSheetProperties': {
                    'properties': {'sheetId': 0, 'title': sheet_names[0]},
                    'fields': 'title'
                }
            }
        ]
        for name in sheet_names[1:]:
            requests.append({'addSheet': {'properties': {'title': name}}})

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        # Share the spreadsheet if email is provided
        if email:
            share_spreadsheet(spreadsheet_id, email)
        
        return spreadsheet_id
    except Exception as e:
        print(f"Error creating spreadsheet: {e}")
        sys.exit(1)

def ensure_sheets_exist(service, spreadsheet_id):
    """既存スプレッドシートに不足しているシートを作成する"""
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        existing_titles = {s['properties']['title'] for s in spreadsheet['sheets']}

        missing = [name for name in REQUIRED_SHEETS if name not in existing_titles]

        if not missing:
            print("All required sheets already exist.")
            return

        requests = [{'addSheet': {'properties': {'title': name}}} for name in missing]
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()

        print(f"Created missing sheets: {', '.join(missing)}")
    except Exception as e:
        print(f"Error ensuring sheets exist: {e}")
        sys.exit(1)


def setup_headers(service, spreadsheet_id):
    """Set up headers for each sheet"""
    try:
        # Data sheet headers
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='data!A1:M1',
            valueInputOption='RAW',
            body={
                'values': [[
                    'datetime', 'userid', 'display_name', 'shokudo_id', 'shokudo_name',
                    'question', 'quadrant', 'answer', 'color', 'attribute',
                    'count', 'count_original', 'photo_file_path'
                ]]
            }
        ).execute()
        
        # Master shokudo headers
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='master_shokudo!A1:B1',
            valueInputOption='RAW',
            body={
                'values': [['shokudo_id', 'shokudo_name']]
            }
        ).execute()
        
        # Master user headers
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='master_user!A1:C1',
            valueInputOption='RAW',
            body={
                'values': [['user_id', 'display_name', 'shokudo_id']]
            }
        ).execute()
        
        # Master quadrant headers
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='master_quadrant!A1:F1',
            valueInputOption='RAW',
            body={
                'values': [[
                    'shokudo_id', 'quadrant_ul', 'quadrant_ur', 
                    'quadrant_ll', 'quadrant_lr', 'question'
                ]]
            }
        ).execute()
        
        # Master color headers
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='master_color!A1:E1',
            valueInputOption='RAW',
            body={
                'values': [['shokudo_id', 'red', 'green', 'blue', 'yellow']]
            }
        ).execute()
        
        print("Headers set up successfully")
    except Exception as e:
        print(f"Error setting up headers: {e}")
        sys.exit(1)

def format_spreadsheet(service, spreadsheet_id):
    """Format the spreadsheet for better readability"""
    try:
        # Format headers in all sheets
        sheets = ['data', 'master_shokudo', 'master_user', 'master_quadrant', 'master_color']
        
        for sheet in sheets:
            # Get the number of columns in the header row
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet}!1:1'
            ).execute()
            
            if 'values' in result:
                num_columns = len(result['values'][0])
                
                # Format header row
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        'requests': [
                            {
                                'repeatCell': {
                                    'range': {
                                        'sheetId': get_sheet_id(service, spreadsheet_id, sheet),
                                        'startRowIndex': 0,
                                        'endRowIndex': 1,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': num_columns
                                    },
                                    'cell': {
                                        'userEnteredFormat': {
                                            'backgroundColor': {
                                                'red': 0.8,
                                                'green': 0.8,
                                                'blue': 0.8
                                            },
                                            'horizontalAlignment': 'CENTER',
                                            'textFormat': {
                                                'bold': True
                                            }
                                        }
                                    },
                                    'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
                                }
                            },
                            {
                                'updateSheetProperties': {
                                    'properties': {
                                        'sheetId': get_sheet_id(service, spreadsheet_id, sheet),
                                        'gridProperties': {
                                            'frozenRowCount': 1
                                        }
                                    },
                                    'fields': 'gridProperties.frozenRowCount'
                                }
                            }
                        ]
                    }
                ).execute()
        
        print("Spreadsheet formatted successfully")
    except Exception as e:
        print(f"Error formatting spreadsheet: {e}")
        # Continue execution even if formatting fails

def get_sheet_id(service, spreadsheet_id, sheet_name):
    """Get the sheet ID for a given sheet name"""
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in spreadsheet['sheets']:
        if sheet['properties']['title'] == sheet_name:
            return sheet['properties']['sheetId']
    return None

def add_sample_data(service, spreadsheet_id):
    """Add sample data to the spreadsheet"""
    try:
        # Add sample shokudo
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='master_shokudo!A:B',
            valueInputOption='RAW',
            body={
                'values': [['sample123', 'サンプルこども食堂']]
            }
        ).execute()
        
        # Add sample quadrant settings
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='master_quadrant!A:F',
            valueInputOption='RAW',
            body={
                'values': [['sample123', 'ごはん', 'あそび', 'おしゃべり', 'べんきょう', 'きょうはなにがたのしかった？']]
            }
        ).execute()
        
        # Add sample color settings
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='master_color!A:E',
            valueInputOption='RAW',
            body={
                'values': [['sample123', '未就学児', '小学生', '中高生', '大人']]
            }
        ).execute()
        
        print("Sample data added successfully")
    except Exception as e:
        print(f"Error adding sample data: {e}")
        # Continue execution even if adding sample data fails

def update_env_file(spreadsheet_id):
    """Update .env file with the spreadsheet ID"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"Warning: {env_file} not found. Creating new file.")
        with open(env_file, 'w') as f:
            f.write(f"SPREADSHEET_ID={spreadsheet_id}\n")
        return
    
    # Read existing .env file
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check if SPREADSHEET_ID already exists
    spreadsheet_id_exists = False
    for i, line in enumerate(lines):
        if line.startswith('SPREADSHEET_ID='):
            lines[i] = f"SPREADSHEET_ID={spreadsheet_id}\n"
            spreadsheet_id_exists = True
            break
    
    # Add SPREADSHEET_ID if it doesn't exist
    if not spreadsheet_id_exists:
        lines.append(f"SPREADSHEET_ID={spreadsheet_id}\n")
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Updated {env_file} with SPREADSHEET_ID={spreadsheet_id}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Initialize Google Sheets for Kodomo Shokudo Survey')
    parser.add_argument('--spreadsheet_id', help='Existing spreadsheet ID to update')
    parser.add_argument('--add_sample', action='store_true', help='Add sample data to the spreadsheet')
    parser.add_argument('--email', help='Email address to share the spreadsheet with')
    args = parser.parse_args()
    
    print("Initializing Google Sheets for Kodomo Shokudo Survey...")
    
    # Create Google Sheets API service
    sheets_service = create_service()
    
    # Create or update spreadsheet
    if args.spreadsheet_id:
        spreadsheet_id = args.spreadsheet_id
        print(f"Using existing spreadsheet with ID: {spreadsheet_id}")
        
        # Share the spreadsheet if email is provided
        if args.email:
            share_spreadsheet(spreadsheet_id, args.email)
    else:
        spreadsheet_id = create_spreadsheet(sheets_service, args.email)
    
    # 不足しているシートを作成してからヘッダーをセットアップ
    ensure_sheets_exist(sheets_service, spreadsheet_id)

    # Set up headers
    setup_headers(sheets_service, spreadsheet_id)
    
    # Format spreadsheet
    format_spreadsheet(sheets_service, spreadsheet_id)
    
    # Add sample data if requested
    if args.add_sample:
        add_sample_data(sheets_service, spreadsheet_id)
    
    # Update .env file
    update_env_file(spreadsheet_id)
    
    print("Initialization complete!")
    print(f"Spreadsheet ID: {spreadsheet_id}")
    print(f"Make sure to set this ID in your .env file as SPREADSHEET_ID={spreadsheet_id}")
    
    if args.email:
        print(f"The spreadsheet has been shared with {args.email}")
    else:
        print("Note: The spreadsheet is owned by the service account and not shared with anyone.")
        print("To share the spreadsheet, run the script again with the --email parameter:")
        print(f"  python init_spreadsheet.py --spreadsheet_id {spreadsheet_id} --email your.email@example.com")

if __name__ == '__main__':
    main()
