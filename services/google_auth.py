"""
Google API 認証の共通ヘルパー (OAuth2)

必要な環境変数:
  GOOGLE_OAUTH_REFRESH_TOKEN
  GOOGLE_OAUTH_CLIENT_ID
  GOOGLE_OAUTH_CLIENT_SECRET
"""

import logging
import os

from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)


def get_google_credentials(scopes=None):
    """OAuth2認証情報を返す"""
    return Credentials(
        token=None,
        refresh_token=os.getenv('GOOGLE_OAUTH_REFRESH_TOKEN'),
        client_id=os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
        token_uri='https://oauth2.googleapis.com/token',
    )
