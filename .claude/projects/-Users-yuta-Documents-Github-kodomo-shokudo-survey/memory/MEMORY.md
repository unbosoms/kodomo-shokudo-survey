# プロジェクトメモリ: こども食堂アンケート集計システム

## 基本情報
- Python/Flask + LINE LIFF + Google Sheets/Drive + OpenCV
- デプロイ先: Google Cloud Run (Dockerコンテナ)
- メインブランチ: `revise-with-copilot` / 開発: `develop`

## 重要ファイル
- `app.py` — 全APIルート定義
- `services/google_auth.py` — Google認証 (GOOGLE_CREDENTIALS優先, フォールバックGOOGLE_SERVICE_ACCOUNT_FILE)
- `services/sheets_service.py` — Google Sheets操作
- `Dockerfile` — gunicorn --workers 1 --threads 8 --timeout 0

## 既知のバグ修正履歴 (コミットログより)
- 色設定の保存が常に失敗するバグ修正済
- こども食堂ドロップダウンのID不一致によるnullエラー修正済
- 登録フォームの初期化エラー修正済
- Cloud Run用Google認証情報の読み込み修正済

## 注意点
- `*.json` が .gitignore 対象だがサービスアカウントキーがリポジトリに含まれる可能性あり
- ローカル開発でLIFFを動かすにはngrokなどHTTPSトンネルが必要
