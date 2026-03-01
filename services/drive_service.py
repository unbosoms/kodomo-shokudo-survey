from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import base64
import logging
import tempfile
import time
import socket

from services.google_auth import get_google_credentials

# Configure logging
logger = logging.getLogger(__name__)


class DriveService:
    def __init__(self):
        """Initialize Google Drive API client"""
        credentials = get_google_credentials()
        self.service = build('drive', 'v3', credentials=credentials)
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        if not self.folder_id:
            logger.warning("GOOGLE_DRIVE_FOLDER_ID environment variable is not set")
    
    def upload_file(self, image_data, filename, max_retries=3):
        """Upload image to Google Drive
        
        Args:
            image_data: Image data (can be file object, bytes, or base64 string)
            filename: Name to give the file in Google Drive
            max_retries: Maximum number of retry attempts
            
        Returns:
            URL to the uploaded file
        """
        start_time = time.time()
        logger.info(f"Starting upload of {filename} to Google Drive")
        
        # Convert image data to bytes
        try:
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # Base64 encoded image
                image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            elif isinstance(image_data, bytes):
                # Already bytes
                image_bytes = image_data
            elif hasattr(image_data, 'read'):
                # File-like object
                image_bytes = image_data.read()
                # Reset file pointer if possible
                if hasattr(image_data, 'seek'):
                    image_data.seek(0)
            else:
                raise ValueError("Unsupported image data format")
            
            logger.info(f"Image data converted to bytes, size: {len(image_bytes) / 1024:.1f} KB")
        except Exception as e:
            logger.error(f"Error converting image data: {e}")
            raise ValueError(f"Failed to process image data: {str(e)}")
        
        # File metadata
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id]
        }

        # 一時ファイルに書き出してから MediaFileUpload でアップロード
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = tmp.name
            logger.info(f"Wrote image to temp file: {tmp_path}")

            media = MediaFileUpload(tmp_path, mimetype='image/jpeg', resumable=False)

            # Upload file with retry logic
            retry_count = 0
            last_exception = None

            while retry_count < max_retries:
                try:
                    logger.info(f"Uploading file to Google Drive (attempt {retry_count + 1}/{max_retries})")

                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()

                    elapsed_time = time.time() - start_time
                    logger.info(f"Upload successful in {elapsed_time:.2f} seconds")
                    return file.get('id')

                except HttpError as e:
                    last_exception = e
                    status_code = e.resp.status
                    logger.warning(f"HTTP error during upload (status {status_code}): {e}")

                    if status_code in [429, 500, 502, 503, 504]:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = min(2 ** retry_count, 60)
                            logger.info(f"Retrying in {wait_time} seconds...")
                            time.sleep(wait_time)
                        else:
                            logger.error("Max retries reached. Upload failed.")
                            raise
                    else:
                        logger.error(f"Non-retryable HTTP error: {e}")
                        raise

                except socket.timeout as e:
                    last_exception = e
                    logger.warning(f"Socket timeout during upload: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 60)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error("Max retries reached. Upload failed.")
                        raise ValueError(f"Connection timeout after {max_retries} attempts: {str(e)}")

                except Exception as e:
                    last_exception = e
                    logger.warning(f"Unexpected error during upload: {e}")
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = min(2 ** retry_count, 60)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error("Max retries reached. Upload failed.")
                        raise

            # If we get here, all retries failed
            elapsed_time = time.time() - start_time
            logger.error(f"Upload failed after {elapsed_time:.2f} seconds and {max_retries} attempts")
            if last_exception:
                raise last_exception
            raise RuntimeError("Upload failed for unknown reason")

        finally:
            # 一時ファイルを必ず削除
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.info(f"Deleted temp file: {tmp_path}")
    
