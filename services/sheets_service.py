from googleapiclient.discovery import build
import os
import datetime
import uuid
import logging

from services.google_auth import get_google_credentials

class SheetsService:
    def __init__(self):
        """Initialize Google Sheets API client"""
        credentials = self._get_credentials()
        self.service = build('sheets', 'v4', credentials=credentials)
        self.spreadsheet_id = os.getenv('SPREADSHEET_ID')
        
        # シート名の定数を追加
        self.sheet_names = {
            'shokudo': 'master_shokudo',
            'user': 'master_user',
            'quadrant': 'master_quadrant',
            'color': 'master_color',
            'data': 'data',
            'color_master': 'master_color_list'  # 新しい色マスターシート
        }

    def _get_credentials(self):
        """Get Google credentials"""
        return get_google_credentials(['https://www.googleapis.com/auth/spreadsheets'])

    def get_all_shokudos(self):
        """Get all children's cafeterias"""
        range_name = f'{self.sheet_names["shokudo"]}!A:B'
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
        range_name = f'{self.sheet_names["shokudo"]}!A:B'
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
        range_name = f'{self.sheet_names["user"]}!A:C'
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
        range_name = f'{self.sheet_names["quadrant"]}!A:F'
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
    
    # 新しいメソッドを追加
    def get_color_master(self):
        """Get master color settings"""
        range_name = f'{self.sheet_names["color_master"]}!A:C'  # A:コード, B:表示名, C:カラーコード
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            colors = {}
            
            # Skip header row
            for row in values[1:]:
                if len(row) >= 3:
                    colors[row[0]] = {
                        'name': row[1],
                        'code': row[2]
                    }
            
            return colors
        except Exception as e:
            logging.error(f"Error getting color master: {e}")
            return {
                'red': {'name': '赤', 'code': '#dc3545'},
                'green': {'name': '緑', 'code': '#198754'},
                'blue': {'name': '青', 'code': '#0d6efd'},
                'yellow': {'name': '黄', 'code': '#ffc107'}
            }  # フォールバック値

    def get_color_settings(self, shokudo_id):
        """Get color settings for a children's cafeteria"""
        range_name = f'{self.sheet_names["color"]}!A:E'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        color_master = self.get_color_master()
        
        for row in values[1:]:  # Skip header
            if len(row) >= 1 and row[0] == shokudo_id:
                settings = {
                    'shokudo_id': row[0],
                    'color_red': row[1] if len(row) >= 2 else '',
                    'color_green': row[2] if len(row) >= 3 else '',
                    'color_blue': row[3] if len(row) >= 4 else '',
                    'color_yellow': row[4] if len(row) >= 5 else '',
                }
                # カラーマスターの情報を追加
                settings['colors'] = color_master
                return settings
        
        # 設定が見つからない場合は空の設定とカラーマスターを返す
        return {
            'shokudo_id': shokudo_id,
            'color_red': '',
            'color_green': '',
            'color_blue': '',
            'color_yellow': '',
            'colors': color_master
        }
    
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
        range_name = 'master_color!A:E'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get('values', [])
        for i, row in enumerate(values[1:], start=2):  # Start from row 2 (after header)
            if len(row) >= 1 and row[0] == shokudo_id:
                # Update existing row
                update_range = f'master_color!A{i}:E{i}'
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=update_range,
                    valueInputOption='RAW',
                    body={'values': [[shokudo_id, red, green, blue, yellow]]}
                ).execute()
                return True

        # No existing row found, append new row
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body={'values': [[shokudo_id, red, green, blue, yellow]]}
        ).execute()
        return True
    
    def record_survey(self, user_id, counts, file_path, event_date=None):
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
        event_date_value = event_date if event_date else now[:10]

        # Map quadrant codes to settings field names
        quadrant_map = {
            'UL': 'quadrant_ul',
            'UR': 'quadrant_ur',
            'LL': 'quadrant_ll',
            'LR': 'quadrant_lr'
        }

        # For each quadrant and color combination, add a row
        for quadrant, colors in counts.items():
            for color, count in colors.items():
                rows.append([
                        now,               # A: datetime（送信日時）
                        event_date_value,  # B: event_date（開催日）
                        user_id,           # C: userid
                        user_info['display_name'],  # D: display_name
                        shokudo_id,        # E: shokudo_id
                        shokudo_info['shokudo_name'],  # F: shokudo_name
                        quadrant_settings['question'],  # G: question
                        f'quadrant_{quadrant}',  # H: quadrant
                        quadrant_settings[quadrant_map[quadrant]],  # I: answer
                        color,             # J: color
                        color_settings[f'color_{color}'],  # K: attribute
                        count,             # L: count
                        count,             # M: count_original
                        file_path          # N: photo_file_path
                    ])

        # Add rows to spreadsheet
        if rows:
            range_name = 'data!A:N'
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

    def get_survey_results(self, shokudo_id):
        """食堂の集計結果を取得し、開催日+質問でグループ化して返す

        data シートの列構成:
          A(0): datetime, B(1): event_date, C(2): userid, D(3): display_name,
          E(4): shokudo_id, F(5): shokudo_name, G(6): question,
          H(7): quadrant, I(8): answer, J(9): color, K(10): attribute,
          L(11): count, M(12): count_original, N(13): photo_file_path

        Returns:
            list: event_date 降順のグループリスト
        """
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='data!A2:N'
        ).execute()
        rows = result.get('values', [])

        # shokudo_id でフィルタ（E列 = index 4）
        rows = [r for r in rows if len(r) > 4 and r[4] == shokudo_id]

        # (event_date, question) でグループ化して count を合算
        groups = {}
        color_order = ['red', 'green', 'blue', 'yellow']

        for row in rows:
            if len(row) < 12:
                continue
            event_date = row[1] if len(row) > 1 else ''
            question   = row[6] if len(row) > 6 else ''
            answer     = row[8] if len(row) > 8 else ''
            color      = row[9] if len(row) > 9 else ''
            attribute  = row[10] if len(row) > 10 else ''
            try:
                count = int(row[11])
            except (ValueError, IndexError):
                count = 0

            key = (event_date, question)
            if key not in groups:
                groups[key] = {
                    'event_date': event_date,
                    'question': question,
                    'answers': [],
                    'colors': [],
                    'table': {}
                }
            g = groups[key]

            if answer and answer not in g['answers']:
                g['answers'].append(answer)

            if color and not any(c['code'] == color for c in g['colors']):
                g['colors'].append({'code': color, 'attribute': attribute})

            if answer not in g['table']:
                g['table'][answer] = {}
            g['table'][answer][color] = g['table'][answer].get(color, 0) + count

        # 色を固定順（red/green/blue/yellow）にソート
        for g in groups.values():
            g['colors'].sort(
                key=lambda c: color_order.index(c['code'])
                if c['code'] in color_order else 99
            )

        # event_date 降順でソート
        return sorted(groups.values(), key=lambda g: g['event_date'], reverse=True)

        return False
