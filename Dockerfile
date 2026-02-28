# ベースイメージ: Python slim で軽量化
FROM python:3.9-slim

# 環境変数設定
# PYTHONDONTWRITEBYTECODE: .pycファイル生成を抑制
# PYTHONUNBUFFERED: ログをリアルタイムで出力
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# OpenCV (headless) が必要とする最小限のシステムライブラリをインストール
# --no-install-recommends で余分なパッケージを排除
# キャッシュ削除でイメージサイズを削減
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係を先にコピーしてキャッシュを活用
# (コードを変えても requirements.txt が変わらなければ再インストール不要)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# セキュリティのため非rootユーザーで実行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Run は PORT 環境変数でポートを指定する
# --workers 1: Cloud Run はコンテナ1つあたりのリソースが限られるため1プロセス
# --threads 8: スレッドで並行リクエストを処理
# --timeout 0: Cloud Runがタイムアウトを管理するためgunicorn側は無効化
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
