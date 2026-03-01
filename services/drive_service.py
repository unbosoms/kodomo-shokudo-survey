from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import os
import io
import base64
import logging
import tempfile
import time
import socket
import httplib2

# Configure logging
logger = logging.getLogger(__name__)

def _get_oauth2_credentials():
    """OAuth2ユーザー認証情報を返す"""
    return Credentials(
        token=None,
        refresh_token=os.getenv('GOOGLE_OAUTH_REFRESH_TOKEN'),
        client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

class DriveService:
    def __init__(self):
        """Initialize Google Drive API client"""
        credentials = _get_oauth2_credentials()
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
    
    def upload_file_from_path(self, file_path, filename=None, max_retries=3):
        """Upload a file from disk to Google Drive
        
        Args:
            file_path: Path to the file on disk
            filename: Name to give the file in Google Drive (defaults to original filename)
            max_retries: Maximum number of retry attempts
            
        Returns:
            URL to the uploaded file
        """
        start_time = time.time()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use original filename if not specified
        if not filename:
            filename = os.path.basename(file_path)
        
        logger.info(f"Starting upload of file {filename} from {file_path}")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size / 1024:.1f} KB")
        
        # File metadata
        file_metadata = {
            'name': filename,
            'parents': [self.folder_id]
        }
        
        # Determine MIME type based on file extension
        mime_type = 'application/octet-stream'  # Default
        if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
        elif file_path.lower().endswith('.png'):
            mime_type = 'image/png'
        elif file_path.lower().endswith('.pdf'):
            mime_type = 'application/pdf'
        
        # Upload file with retry logic
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                logger.info(f"Uploading file to Google Drive (attempt {retry_count + 1}/{max_retries})")
                
                # Create media upload
                with open(file_path, 'rb') as f:
                    media = MediaIoBaseUpload(
                        f,
                        mimetype=mime_type,
                        resumable=True
                    )
                    
                    # Upload file
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id,webViewLink'
                    ).execute()
                
                elapsed_time = time.time() - start_time
                logger.info(f"Upload successful in {elapsed_time:.2f} seconds")
                
                # Return the web view link
                return file.get('webViewLink')
                
            except HttpError as e:
                last_exception = e
                status_code = e.resp.status
                logger.warning(f"HTTP error during upload (status {status_code}): {e}")
                
                # Only retry on certain status codes
                if status_code in [429, 500, 502, 503, 504]:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff
                        wait_time = min(2 ** retry_count, 60)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries reached. Upload failed.")
                        raise
                else:
                    # Don't retry on client errors
                    logger.error(f"Non-retryable HTTP error: {e}")
                    raise
                    
            except socket.timeout as e:
                last_exception = e
                logger.warning(f"Socket timeout during upload: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = min(2 ** retry_count, 60)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached. Upload failed.")
                    raise ValueError(f"Connection timeout after {max_retries} attempts: {str(e)}")
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error during upload: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = min(2 ** retry_count, 60)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached. Upload failed.")
                    raise
        
        # If we get here, all retries failed
        elapsed_time = time.time() - start_time
        logger.error(f"Upload failed after {elapsed_time:.2f} seconds and {max_retries} attempts")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Upload failed for unknown reason")
    
    def list_files(self, max_results=10, max_retries=3):
        """List files in the configured folder
        
        Args:
            max_results: Maximum number of files to return
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of file metadata
        """
        logger.info(f"Listing files in folder {self.folder_id}")
        
        # Query for files in the folder
        query = f"'{self.folder_id}' in parents"
        
        # Retry logic
        retry_count = 0
        last_exception = None
        
        while retry_count < max_retries:
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=max_results,
                    fields="files(id, name, webViewLink, createdTime)"
                ).execute()
                
                files = results.get('files', [])
                logger.info(f"Found {len(files)} files in folder")
                return files
                
            except HttpError as e:
                last_exception = e
                status_code = e.resp.status
                logger.warning(f"HTTP error during list_files (status {status_code}): {e}")
                
                # Only retry on certain status codes
                if status_code in [429, 500, 502, 503, 504]:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff
                        wait_time = min(2 ** retry_count, 60)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries reached. list_files failed.")
                        raise
                else:
                    # Don't retry on client errors
                    logger.error(f"Non-retryable HTTP error: {e}")
                    raise
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Unexpected error during list_files: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = min(2 ** retry_count, 60)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached. list_files failed.")
                    raise
        
        # If we get here, all retries failed
        logger.error(f"list_files failed after {max_retries} attempts")
        if last_exception:
            raise last_exception
        else:
            return []  # Return empty list as fallback
    
    def delete_file(self, file_id, max_retries=3):
        """Delete a file from Google Drive
        
        Args:
            file_id: ID of the file to delete
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting file with ID {file_id}")
        
        # Retry logic
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.service.files().delete(fileId=file_id).execute()
                logger.info(f"File {file_id} deleted successfully")
                return True
                
            except HttpError as e:
                status_code = e.resp.status
                logger.warning(f"HTTP error during delete_file (status {status_code}): {e}")
                
                # If file not found, consider it a success
                if status_code == 404:
                    logger.info(f"File {file_id} not found, considering delete successful")
                    return True
                
                # Only retry on certain status codes
                if status_code in [429, 500, 502, 503, 504]:
                    retry_count += 1
                    if retry_count < max_retries:
                        # Exponential backoff
                        wait_time = min(2 ** retry_count, 60)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Max retries reached. delete_file failed.")
                        return False
                else:
                    # Don't retry on client errors
                    logger.error(f"Non-retryable HTTP error: {e}")
                    return False
                    
            except Exception as e:
                logger.warning(f"Unexpected error during delete_file: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = min(2 ** retry_count, 60)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached. delete_file failed: {e}")
                    return False
        
        # If we get here, all retries failed
        logger.error(f"delete_file failed after {max_retries} attempts")
        return False
