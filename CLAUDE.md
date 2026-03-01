# CLAUDE.md - こども食堂アンケート集計システム

## プロジェクト概要

LINE公式アカウントと連携したLIFFアプリで、こども食堂の参加者アンケートを集計するシステム。
参加者がシールを貼ったアンケート用紙を撮影すると、OpenCVでシールの色・位置を自動カウントし結果を表示する。

## 技術スタック

| 層 | 技術 |
|---|---|
| バックエンド | Python 3.9 / Flask 2.0 |
| フロントエンド | HTML / CSS / JavaScript / Bootstrap |
| LINE連携 | LINE Messaging API (SDK v2) / LIFF |
| データ保存 | Google Sheets API v4 |
| 画像保存 | Google Drive API v3 |
| 画像処理 | OpenCV (headless) / NumPy / Pillow |
| 認証 | Google OAuth2 (Drive・Sheets共通) |
| 本番サーバー | Gunicorn |
| コンテナ | Docker (python:3.9-slim) |

## ディレクトリ構造

```
kodomo-shokudo-survey/
├── app.py                  # Flaskエントリーポイント・全APIルート定義
├── requirements.txt        # pip依存関係
├── pyproject.toml          # プロジェクトメタデータ
├── Dockerfile              # Cloud Run用コンテナ定義
├── .env                    # 環境変数 (gitignore済)
├── .env.template           # 環境変数テンプレート
├── services/               # サービスレイヤー
│   ├── google_auth.py      # Google OAuth2認証共通ヘルパー
│   ├── sheets_service.py   # Google Sheets操作
│   ├── drive_service.py    # Google Drive操作
│   ├── image_service.py    # 画像処理 (OpenCV)
│   └── line_service.py     # LINE Messaging API
├── templates/              # Jinja2 HTMLテンプレート
│   ├── index.html          # LIFF メインページ
│   └── admin.html          # 管理画面
├── static/                 # 静的ファイル
│   ├── js/
│   ├── css/
│   └── img/
├── init_spreadsheet.py     # スプレッドシート初期化スクリプト
├── init_drive.py           # Google Drive初期化スクリプト
├── generate_test_image.py  # テスト画像生成スクリプト
├── test_app.py             # アプリ統合テスト
├── test_image_processing.py# 画像処理単体テスト
└── test_line_webhook.py    # LINE Webhookテスト
```

## 環境変数

`.env.template` を `.env` にコピーして設定する。

```env
# LINE API
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=
LIFF_ID=

# Google OAuth2 (Drive・Sheets共通)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REFRESH_TOKEN=

# Google リソース
SPREADSHEET_ID=
GOOGLE_DRIVE_FOLDER_ID=

# Flask
FLASK_ENV=development
FLASK_DEBUG=1
```

### Google認証について (`services/google_auth.py`)
- Drive・Sheets ともに OAuth2 ユーザー認証を使用
- リフレッシュトークンは `get_refresh_token.py` で取得（実行後は削除してよい）
- スコープ: `drive.file` + `spreadsheets`
- Cloud Run環境でも同じ環境変数を設定すること（Secret Manager推奨）

### リフレッシュトークンの再取得
```bash
# .env に GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET を設定した上で実行
.venv/bin/python get_refresh_token.py
# → ブラウザで認証後、GOOGLE_OAUTH_REFRESH_TOKEN を .env に設定
# → 実行後は get_refresh_token.py を削除
```

## Google Sheetsのシート構成

| シート名 | 内容 |
|---|---|
| `master_shokudo` | こども食堂マスタ (ID, 名前, 住所, 緯度経度) |
| `master_user` | ユーザーマスタ (LINE ID, 氏名, 食堂ID) |
| `master_quadrant` | 4象限ラベル設定 (質問文, UL/UR/LL/LR) |
| `master_color` | 色の意味設定 (赤/緑/青/黄) |
| `master_color_list` | 色マスタ |
| `data` | アンケート集計データ |

### `data` シートの列構成 (A〜N)

| 列 | 項目 | 内容 |
|---|---|---|
| A | datetime | 送信日時 |
| B | event_date | 開催日（ユーザーが選択） |
| C | userid | LINE ユーザーID |
| D | display_name | ユーザー表示名 |
| E | shokudo_id | こども食堂ID |
| F | shokudo_name | こども食堂名 |
| G | question | 質問文 |
| H | quadrant | 象限コード (quadrant_UL 等) |
| I | answer | 象限ラベル |
| J | color | 色コード (red 等) |
| K | attribute | 色の意味 |
| L | count | シール個数 |
| M | count_original | シール個数（元値） |
| N | photo_file_path | Google Drive ファイルID |

※ 0件の組み合わせも全行記録する。

## APIエンドポイント (`app.py`)

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | LIFFメインページ |
| GET | `/admin` | 管理画面 |
| POST | `/webhook` | LINE Webhookハンドラ |
| POST | `/api/upload` | 画像アップロード・処理 |
| POST | `/api/check-user` | ユーザー登録確認 |
| POST | `/api/register-user` | ユーザー登録 |
| POST | `/api/register-shokudo` | こども食堂登録 |
| POST | `/api/update-quadrant` | 4象限設定更新 |
| POST | `/api/update-color` | 色設定更新 |
| GET | `/api/get-shokudos` | 全食堂一覧取得 |
| GET | `/api/get-settings` | 食堂の設定取得 |
| GET | `/api/guide-overlay` | カメラガイドオーバーレイ画像生成 |
| GET | `/survey-template` | アンケート用紙テンプレート |

## ローカル開発

```bash
# 仮想環境のセットアップ (初回)
bash setup.sh

# または手動で:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 環境変数設定
cp .env.template .env
# .env を編集して各種キーを設定

# 開発サーバー起動
python app.py
# → http://localhost:5000
```

## 初期セットアップ (Googleリソース作成)

```bash
# スプレッドシート作成・初期化
python init_spreadsheet.py --add_sample --email your.email@example.com

# Google Driveフォルダ作成
python init_drive.py --email your.email@example.com
```

スクリプト実行後、生成された `SPREADSHEET_ID` と `GOOGLE_DRIVE_FOLDER_ID` が `.env` に自動追記される。

## テスト

```bash
# 統合テスト
python test_app.py

# 画像処理テスト (テスト画像を先に生成)
python generate_test_image.py --output test_image.jpg
python test_image_processing.py --image_path test_image.jpg

# LINE Webhookシミュレーション (ローカルサーバー起動後)
python test_line_webhook.py --message "アンケート" --user_id "test_user_id"
```

## デプロイ

### Cloud Run (現在の本番環境)

ソースコードから直接デプロイ（推奨）:
```bash
gcloud run deploy kodomo-shokudo-survey \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

環境変数を追加・更新する場合（既存の変数を保持したまま更新）:
```bash
gcloud run services update kodomo-shokudo-survey \
  --region asia-northeast1 \
  --update-env-vars "KEY=VALUE"
```

> ⚠️ `--set-env-vars` は既存の全変数を置き換えるため、1つだけ変更したい場合は必ず `--update-env-vars` を使うこと。

Gunicornの設定 (Dockerfile CMD):
- `--workers 1` — Cloud Runのリソース制限に合わせて1プロセス
- `--threads 8` — スレッドで並行処理
- `--timeout 0` — Cloud Runがタイムアウトを管理

## 既知のセキュリティ課題

小規模・知人向け運用を前提としているが、以下の課題が未対応。将来的に対処が必要。

### 🔴 優先度高

| 問題 | 該当箇所 | 内容 |
|---|---|---|
| 管理画面に認証なし | `app.py` `/admin` | URLを知っていれば誰でもアクセス可能 |
| 管理APIに認証なし | `app.py` `/api/update-quadrant` `/api/update-color` `/api/register-shokudo` | 他の食堂の設定を誰でも書き換え可能 |

### 🟡 優先度中

| 問題 | 該当箇所 | 内容 |
|---|---|---|
| XSSリスク | `static/js/admin.js` | スプレッドシートのデータを `innerHTML` で直接挿入 |
| エラーメッセージが詳細 | `app.py` 各エラー処理 | `str(e)` をそのままレスポンスに返しており内部情報が漏洩する可能性 |
| ファイルタイプ検証なし | `app.py` `/api/upload` | MIMEタイプ・拡張子チェックなし（サイズ制限のみ） |
| レート制限なし | 全APIエンドポイント | 短時間の大量リクエストでGoogle APIのクォータを消費させられる可能性 |

### 🟢 対処済み・非該当

- SQLインジェクション → Google Sheets APIを使用しているため非該当
- 一時ファイル漏洩 → `finally` で確実に削除済み
- Dockerの権限 → 非rootユーザー（appuser）で実行済み
- デバッグ用コンソールログ → `debug.js` 削除済み

## 注意事項

## python環境
- uvを使ってvenv環境を構築しています。
- pythonコードを実行したい場合は「.venv/bin/python」コマンドを利用してください。

### セキュリティ
- `.env` は `.gitignore` で除外済み — **認証情報をコミットしない**
- OAuth2認証情報（CLIENT_ID / CLIENT_SECRET / REFRESH_TOKEN）はCloud Runの環境変数またはSecret Managerで管理する

### ブランチ戦略
- `main` ブランチ: `revise-with-copilot`
- 開発ブランチ: `develop`
- PRは `revise-with-copilot` ブランチに向けて作成する

### 画像処理の制限
- アップロード上限: 16MB (`MAX_CONTENT_LENGTH`)
- OpenCVはheadlessビルドを使用 (`opencv-python-headless`)
- Dockerイメージに `libglib2.0-0` と `libgomp1` が必要

### Google Sheets接続エラー
- `ConnectionResetError` は503で返すように実装済み
- クォータ超過時は指数バックオフを検討

### LINE LIFF
- `LIFF_ID` 環境変数が必要
- ローカル開発時はngrokなどでHTTPSトンネルが必要 (LIFFはHTTPS必須)
