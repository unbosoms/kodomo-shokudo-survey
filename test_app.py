import unittest
import os
import sys
import json
from app import app

class TestApp(unittest.TestCase):
    """Test cases for the Flask application"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test the index route"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'LIFF', response.data)
    
    def test_admin_route(self):
        """Test the admin route"""
        response = self.app.get('/admin')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'admin', response.data.lower())
    
    def test_static_route(self):
        """Test the static files route"""
        response = self.app.get('/static/css/style.css')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'body', response.data)
    
    def test_api_get_shokudos(self):
        """Test the get_shokudos API endpoint"""
        # This test may fail if Google Sheets API is not configured
        # It's included as an example of how to test API endpoints
        response = self.app.get('/api/get-shokudos')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
    
    def test_api_check_user_missing_params(self):
        """Test the check_user API endpoint with missing parameters"""
        response = self.app.post('/api/check-user', 
                                json={},
                                content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_api_guide_overlay(self):
        """Test the guide overlay API endpoint"""
        response = self.app.get('/api/guide-overlay?width=100&height=100')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        self.assertTrue(len(response.data) > 0)

def check_environment():
    """Check if the environment is properly set up"""
    required_vars = [
        'LINE_CHANNEL_SECRET',
        'LINE_CHANNEL_ACCESS_TOKEN',
        'LIFF_ID',
        'GOOGLE_SERVICE_ACCOUNT_FILE',
        'SPREADSHEET_ID',
        'GOOGLE_DRIVE_FOLDER_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("WARNING: The following environment variables are missing:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nTests that require these variables may fail.")
        print("Please set these variables in your .env file.")
    else:
        print("All required environment variables are set.")
    
    # Check if Google service account file exists
    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if service_account_file and not os.path.exists(service_account_file):
        print(f"\nWARNING: Google service account file not found at {service_account_file}")
        print("Tests that require Google API access may fail.")

if __name__ == '__main__':
    print("Checking environment...")
    check_environment()
    
    print("\nRunning tests...")
    unittest.main()
