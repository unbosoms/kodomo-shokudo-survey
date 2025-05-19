from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import datetime
import uuid

class SheetsService:
    def __init__(self):
        """Initialize Google Sheets API client"""
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE'),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
    
    def get_all_shokudos(self):
        """Get all children's cafeterias"""
        range_name = 'master_shokudo!A:B'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        shokudos = []
        
        # Skip header row
        for row in values[1:]:
            if len(row) >= 2:
                shokudos.append({
                    'shokudo_id': row[0],
                    'shokudo_name': row[1]
                })
        
        return shokudos
    
    def get_shokudo_info(self, shokudo_id):
        """Get information for a specific children's cafeteria"""
        range_name = 'master_shokudo!A:B'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        for row in values[1:]:  # Skip header
            if len(row) >= 1 and row[0] == shokudo_id:
                return {
                    'shokudo_id': row[0],
                    'shokudo_name': row[1] if len(row) >= 2 else ''
                }
        
        return None
    
    def get_user_info(self, user_id):
        """Get user information"""
        range_name = 'master_user!A:C'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        for row in values[1:]:  # Skip header
            if len(row) >= 1 and row[0] == user_id:
                return {
                    'user_id': row[0],
                    'display_name': row[1] if len(row) >= 2 else '',
                    'shokudo_id': row[2] if len(row) >= 3 else ''
                }
        
        return None
    
    def get_quadrant_settings(self, shokudo_id):
        """Get quadrant settings for a children's cafeteria"""
        range_name = 'master_quadrant!A:F'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        for row in values[1:]:  # Skip header
            if len(row) >= 1 and row[0] == shokudo_id:
                return {
                    'shokudo_id': row[0],
                    'quadrant_ul': row[1] if len(row) >= 2 else '',
                    'quadrant_ur': row[2] if len(row) >= 3 else '',
                    'quadrant_ll': row[3] if len(row) >= 4 else '',
                    'quadrant_lr': row[4] if len(row) >= 5 else '',
                    'question': row[5] if len(row) >= 6 else ''
                }
        
        return None
    
    def get_color_settings(self, shokudo_id):
        """Get color settings for a children's cafeteria"""
        range_name = 'master_color!A:E'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        for row in values[1:]:  # Skip header
            if len(row) >= 1 and row[0] == shokudo_id:
                return {
                    'shokudo_id': row[0],
                    'red': row[1] if len(row) >= 2 else '',
                    'green': row[2] if len(row) >= 3 else '',
                    'blue': row[3] if len(row) >= 4 else '',
                    'yellow': row[4] if len(row) >= 5 else ''
                }
        
        return None
    
    def register_user(self, user_id, display_name, shokudo_id):
        """Register a new user"""
        # Check if user already exists
        existing_user = self.get_user_info(user_id)
        if existing_user:
            # Update existing user
            range_name = 'master_user!A:C'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (after header)
                if len(row) >= 1 and row[0] == user_id:
                    # Update row
                    update_range = f'master_user!A{i}:C{i}'
                    update_body = {
                        'values': [[user_id, display_name, shokudo_id]]
                    }
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=update_body
                    ).execute()
                    return True
            
            return False
        else:
            # Add new user
            range_name = 'master_user!A:C'
            body = {
                'values': [[user_id, display_name, shokudo_id]]
            }
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
    
    def register_shokudo(self, shokudo_name, address='', latitude='', longitude=''):
        """Register a new children's cafeteria"""
        # Generate unique ID
        shokudo_id = str(uuid.uuid4())[:8]
        
        # Add to spreadsheet
        range_name = 'master_shokudo!A:B'
        body = {
            'values': [[shokudo_id, shokudo_name]]
        }
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        return shokudo_id
    
    def update_quadrant(self, shokudo_id, question, quadrant_ul, quadrant_ur, quadrant_ll, quadrant_lr):
        """Update quadrant settings"""
        # Check if settings already exist
        existing_settings = self.get_quadrant_settings(shokudo_id)
        if existing_settings:
            # Update existing settings
            range_name = 'master_quadrant!A:F'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (after header)
                if len(row) >= 1 and row[0] == shokudo_id:
                    # Update row
                    update_range = f'master_quadrant!A{i}:F{i}'
                    update_body = {
                        'values': [[shokudo_id, quadrant_ul, quadrant_ur, quadrant_ll, quadrant_lr, question]]
                    }
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=update_body
                    ).execute()
                    return True
            
            return False
        else:
            # Add new settings
            range_name = 'master_quadrant!A:F'
            body = {
                'values': [[shokudo_id, quadrant_ul, quadrant_ur, quadrant_ll, quadrant_lr, question]]
            }
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
    
    def update_color(self, shokudo_id, red, green, blue, yellow):
        """Update color settings"""
        # Check if settings already exist
        existing_settings = self.get_color_settings(shokudo_id)
        if existing_settings:
            # Update existing settings
            range_name = 'master_color!A:E'
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            for i, row in enumerate(values[1:], start=2):  # Start from row 2 (after header)
                if len(row) >= 1 and row[0] == shokudo_id:
                    # Update row
                    update_range = f'master_color!A{i}:E{i}'
                    update_body = {
                        'values': [[shokudo_id, red, green, blue, yellow]]
                    }
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=update_range,
                        valueInputOption='RAW',
                        body=update_body
                    ).execute()
                    return True
            
            return False
        else:
            # Add new settings
            range_name = 'master_color!A:E'
            body = {
                'values': [[shokudo_id, red, green, blue, yellow]]
            }
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
    
    def record_survey(self, user_id, counts, file_path):
        """Record survey results in spreadsheet"""
        user_info = self.get_user_info(user_id)
        if not user_info or not user_info['shokudo_id']:
            return False
            
        shokudo_id = user_info['shokudo_id']
        shokudo_info = self.get_shokudo_info(shokudo_id)
        quadrant_settings = self.get_quadrant_settings(shokudo_id)
        color_settings = self.get_color_settings(shokudo_id)
        
        if not shokudo_info or not quadrant_settings or not color_settings:
            return False
        
        # Create data rows
        rows = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Map quadrant codes to settings field names
        quadrant_map = {
            'UL': 'quadrant_ul',
            'UR': 'quadrant_ur',
            'LL': 'quadrant_ll',
            'LR': 'quadrant_lr'
        }
        
        # For each quadrant and color combination with count > 0, add a row
        for quadrant, colors in counts.items():
            for color, count in colors.items():
                if count > 0:
                    rows.append([
                        now,  # datetime
                        user_id,  # userid
                        user_info['display_name'],  # display_name
                        shokudo_id,  # shokudo_id
                        shokudo_info['shokudo_name'],  # shokudo_name
                        quadrant_settings['question'],  # question
                        f'quadrant_{quadrant}',  # quadrant
                        quadrant_settings[quadrant_map[quadrant]],  # answer
                        color,  # color
                        color_settings[color],  # attribute
                        count,  # count
                        count,  # count_original
                        file_path  # photo_file_path
                    ])
        
        # Add rows to spreadsheet
        if rows:
            range_name = 'data!A:M'
            body = {
                'values': rows
            }
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            return True
        
        return False
