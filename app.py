from flask import Flask, request, render_template, jsonify, send_from_directory, Response
from services.line_service import LineService
from services.image_service import ImageService
from services.sheets_service import SheetsService
from services.drive_service import DriveService
import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app with increased max content length (16MB)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize services
line_service = LineService()
image_service = ImageService()
sheets_service = SheetsService()
drive_service = DriveService()

@app.route('/')
def index():
    """Main LIFF page"""
    return render_template('index.html', liff_id=os.getenv('LIFF_ID'))

@app.route('/admin')
def admin():
    """Admin page for managing children's cafeterias"""
    return render_template('admin.html', liff_id=os.getenv('LIFF_ID'))

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/webhook', methods=['POST'])
def webhook():
    """LINE Webhook handler"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        line_service.handle_webhook(body, signature)
    except Exception as e:
        app.logger.error(f"Webhook error: {e}")
        
    return 'OK'

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Image upload API"""
    start_time = time.time()
    logger.info("Upload request received")
    
    user_id = request.form.get('userId')
    shokudo_id = request.form.get('shokudoId')
    image_file = request.files.get('image')
    
    if not user_id or not image_file:
        logger.warning(f"Missing parameters: user_id={user_id}, image_file={'present' if image_file else 'missing'}")
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    try:
        # Log file size
        image_file.seek(0, os.SEEK_END)
        file_size = image_file.tell()
        image_file.seek(0)
        logger.info(f"Processing image of size {file_size / 1024:.1f} KB")
        
        # Process image with timeout handling
        try:
            # Process image
            logger.info("Processing image...")
            processed_image, counts = image_service.process_image(image_file)
            logger.info(f"Image processed successfully. Counts: {counts}")
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return jsonify({'success': False, 'error': f'Image processing error: {str(e)}'}), 500
        
        # Upload to Google Drive with timeout handling
        try:
            logger.info("Uploading to Google Drive...")
            file_path = drive_service.upload_file(processed_image, f"survey_{user_id}_{int(time.time())}.jpg")
            logger.info(f"Uploaded to Google Drive: {file_path}")
        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {e}")
            return jsonify({'success': False, 'error': f'Google Drive upload error: {str(e)}'}), 500
        
        # Record in Google Sheets
        try:
            logger.info("Recording in Google Sheets...")
            sheets_service.record_survey(user_id, counts, file_path)
            logger.info("Recorded in Google Sheets successfully")
        except Exception as e:
            logger.error(f"Error recording in Google Sheets: {e}")
            # Continue even if sheets recording fails, as we already have the image and counts
        
        # Send LINE notification
        try:
            logger.info("Sending LINE notification...")
            user_profile = line_service.get_profile(user_id)
            line_service.send_survey_result(user_id, counts, user_profile)
            logger.info("LINE notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending LINE notification: {e}")
            # Continue even if notification fails, as we already have the image and counts
        
        elapsed_time = time.time() - start_time
        logger.info(f"Upload completed successfully in {elapsed_time:.2f} seconds")
        return jsonify({'success': True, 'counts': counts})
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Upload failed after {elapsed_time:.2f} seconds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/check-user', methods=['POST'])
def check_user():
    """Check user registration status"""
    data = request.json
    user_id = data.get('userId')
    display_name = data.get('displayName')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'Missing userId'}), 400
    
    # Check if user is admin (based on ADMIN_USERS in .env file)
    # Format in .env: ADMIN_USERS=user_id1,user_id2,user_id3
    admin_users_str = os.getenv('ADMIN_USERS', '')
    logger.info(f"Raw ADMIN_USERS from env: '{admin_users_str}'")
    
    # Split and clean up admin users list
    admin_users = [u.strip() for u in admin_users_str.split(',') if u.strip()]
    logger.info(f"Processed admin users list: {admin_users}")
    
    # Check if user is in admin list
    is_admin = user_id in admin_users
    logger.info(f"Checking user '{user_id}' (admin: {is_admin})")
    
    # Additional debug for exact comparison
    for admin_id in admin_users:
        logger.info(f"Comparing: '{user_id}' == '{admin_id}' : {user_id == admin_id}")
    
    # If user is admin, we don't need to check registration
    if is_admin:
        logger.info(f"User {user_id} is an admin")
        return jsonify({
            'success': True,
            'isRegistered': True,
            'isAdmin': True,
            'user': {
                'user_id': user_id,
                'display_name': display_name,
                'shokudo_id': 'admin'  # Placeholder
            },
            'shokudo': {
                'shokudo_id': 'admin',
                'shokudo_name': 'Admin'
            }
        })
    
    # Check if user is registered
    user_info = sheets_service.get_user_info(user_id)
    
    if user_info:
        # User is registered
        shokudo_info = sheets_service.get_shokudo_info(user_info['shokudo_id'])
        return jsonify({
            'success': True,
            'isRegistered': True,
            'isAdmin': False,
            'user': user_info,
            'shokudo': shokudo_info
        })
    else:
        # User is not registered
        return jsonify({
            'success': True,
            'isRegistered': False,
            'isAdmin': False
        })

@app.route('/api/register-user', methods=['POST'])
def register_user():
    """Register a new user"""
    data = request.json
    user_id = data.get('userId')
    display_name = data.get('displayName')
    shokudo_id = data.get('shokudoId')
    
    if not user_id or not display_name or not shokudo_id:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    success = sheets_service.register_user(user_id, display_name, shokudo_id)
    
    return jsonify({'success': success})

@app.route('/api/register-shokudo', methods=['POST'])
def register_shokudo():
    """Register a new children's cafeteria (admin only)"""
    data = request.json
    shokudo_name = data.get('shokudoName')
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if not shokudo_name:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    shokudo_id = sheets_service.register_shokudo(shokudo_name, address, latitude, longitude)
    
    return jsonify({'success': True, 'shokudoId': shokudo_id})

@app.route('/api/update-quadrant', methods=['POST'])
def update_quadrant():
    """Update quadrant settings"""
    data = request.json
    shokudo_id = data.get('shokudoId')
    question = data.get('question')
    quadrant_ul = data.get('quadrantUL')
    quadrant_ur = data.get('quadrantUR')
    quadrant_ll = data.get('quadrantLL')
    quadrant_lr = data.get('quadrantLR')
    
    if not shokudo_id or not question or not quadrant_ul or not quadrant_ur or not quadrant_ll or not quadrant_lr:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    success = sheets_service.update_quadrant(shokudo_id, question, quadrant_ul, quadrant_ur, quadrant_ll, quadrant_lr)
    
    return jsonify({'success': success})

@app.route('/api/update-color', methods=['POST'])
def update_color():
    """Update color settings"""
    data = request.json
    shokudo_id = data.get('shokudoId')
    red = data.get('red')
    green = data.get('green')
    blue = data.get('blue')
    yellow = data.get('yellow')
    
    if not shokudo_id or not red or not green or not blue or not yellow:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
    
    success = sheets_service.update_color(shokudo_id, red, green, blue, yellow)
    
    return jsonify({'success': success})

@app.route('/api/get-shokudos', methods=['GET'])
def get_shokudos():
    """Get all children's cafeterias"""
    shokudos = sheets_service.get_all_shokudos()
    
    return jsonify({'success': True, 'shokudos': shokudos})

@app.route('/api/get-settings', methods=['GET'])
def get_settings():
    """Get settings for a children's cafeteria"""
    shokudo_id = request.args.get('shokudoId')
    
    if not shokudo_id:
        return jsonify({'success': False, 'error': 'Missing shokudoId'}), 400
    
    quadrant_settings = sheets_service.get_quadrant_settings(shokudo_id)
    color_settings = sheets_service.get_color_settings(shokudo_id)
    
    return jsonify({
        'success': True,
        'quadrant': quadrant_settings,
        'color': color_settings
    })

@app.route('/api/guide-overlay', methods=['GET'])
def guide_overlay():
    """Generate guide overlay for camera"""
    width = request.args.get('width', default=640, type=int)
    height = request.args.get('height', default=480, type=int)
    
    # Generate overlay
    overlay_data = image_service.create_guide_overlay(width, height)
    
    # Return as PNG image
    return Response(overlay_data, mimetype='image/png')

@app.route('/survey-template')
def survey_template():
    """Serve the survey template HTML page"""
    return send_from_directory('static/img', 'survey_template.html')

if __name__ == '__main__':
    app.run(debug=True)
