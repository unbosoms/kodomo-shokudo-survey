"""
Google API 認証の共通ヘルパー

優先順位:
  1. GOOGLE_CREDENTIALS  - JSON文字列 (Cloud Run / Secret Manager)
  2. GOOGLE_SERVICE_ACCOUNT_FILE - ファイルパス (ローカル開発)
"""

import json
import logging
import os

from google.oauth2 import service_account

logger = logging.getLogger(__name__)


def get_google_credentials(scopes: list):
    """指定スコープで Google サービスアカウント認証情報を返す"""

    # --- Cloud Run: Secret Manager で環境変数に JSON 文字列を注入 ---
    credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    if credentials_json:
        try:
            info = json.loads(credentials_json)
            logger.info("Using GOOGLE_CREDENTIALS (JSON string) for authentication")
            return service_account.Credentials.from_service_account_info(info, scopes=scopes)
        except Exception as e:
            raise ValueError(f"GOOGLE_CREDENTIALS の解析に失敗しました: {e}") from e

    # --- ローカル開発: サービスアカウント JSON ファイル ---
    credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if credentials_file:
        if not os.path.exists(credentials_file):
            raise FileNotFoundError(
                f"GOOGLE_SERVICE_ACCOUNT_FILE で指定されたファイルが見つかりません: {credentials_file}"
            )
        logger.info("Using GOOGLE_SERVICE_ACCOUNT_FILE for authentication")
        return service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)

    raise ValueError(
        "Google 認証情報が見つかりません。"
        "GOOGLE_CREDENTIALS または GOOGLE_SERVICE_ACCOUNT_FILE を設定してください。"
    )
