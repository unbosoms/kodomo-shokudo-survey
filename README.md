# こども食堂アンケート集計システム

LINE公式アカウントと連携したLIFFアプリを使用して、こども食堂の参加者アンケートを集計するシステムです。参加者がシールを貼ったアンケート用紙の写真を撮影し、自動的にシールの数をカウントして集計結果を表示します。

## 機能

### 1. こども食堂登録機能
- 管理者がこども食堂を登録できます
- こども食堂の名前、住所、緯度、経度を入力し、自動的にユニークなIDを採番します

### 2. ユーザー登録機能
- こども食堂の運営者がユーザーとして登録できます
- LINE IDと氏名、所属するこども食堂を登録します
- LINE IDはLIFFアプリの仕組みを使って自動的に取得します

### 3. 質問と色の意味を設定する機能
- こども食堂ごとに質問文と4つの回答選択肢を設定できます
- シールの色（赤、緑、青、黄）が何を示しているかも設定できます
- 例：
  - 質問文：きょうはなにがたのしかった？
  - 回答選択肢：ごはん、あそび、おしゃべり、べんきょう
  - 色の意味：未就学児、小学生、中高生、大人

### 4. 写真アップロード機能
- シールを張った紙の写真を撮影し、シールの数をカウントします
- 紙は縦横それぞれ2分割の合計4つのエリアを持ち、各エリアに回答選択肢が割り当てられています
- 撮影時には縦横4分割のガイド線が表示されます
- 写真の処理機能：
  - ホワイトバランスの調整
  - 影の除去
  - 台形補正（斜めから撮影された場合）
  - 背景除去
  - シールの色別カウント

## 技術スタック

- **バックエンド**: Python, Flask
- **フロントエンド**: HTML, CSS, JavaScript, Bootstrap
- **LINE連携**: LINE Messaging API, LIFF (LINE Front-end Framework)
- **データ保存**: Google Sheets API
- **画像保存**: Google Drive API
- **画像処理**: OpenCV, NumPy
- **デプロイ**: Vercel

## セットアップ手順

### 前提条件
- Python 3.8以上
- LINE Developersアカウント
- Google Cloud Platformアカウント

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/kodomo-shokudo-survey.git
cd kodomo-shokudo-survey
```

### 2. 仮想環境の作成とパッケージのインストール
```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 環境変数の設定
`.env.template`ファイルを`.env`にコピーし、必要な情報を入力します：

```bash
cp .env.template .env
```

`.env`ファイルに以下の情報を設定します：
- LINE API認証情報
- Google API認証情報
- その他の設定

### 4. Google APIの設定
1. Google Cloud Platformでプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. サービスアカウントを作成し、キーファイルをダウンロード
4. キーファイルをプロジェクトディレクトリに配置し、`.env`ファイルで指定
5. スプレッドシートの初期化スクリプトを実行:
   ```bash
   python init_spreadsheet.py --add_sample --email your.email@example.com
   ```
   このスクリプトは必要なシートとヘッダーを持つスプレッドシートを作成し、サンプルデータを追加します。
   スプレッドシートIDは自動的に`.env`ファイルに追加されます。
   `--email`パラメータを指定すると、作成されたスプレッドシートが指定したメールアドレスと共有されます。
   これにより、サービスアカウントが所有するスプレッドシートにアクセスできるようになります。
6. Google Driveフォルダの初期化スクリプトを実行:
   ```bash
   python init_drive.py --email your.email@example.com
   ```
   このスクリプトは写真を保存するためのGoogle Driveフォルダを作成し、フォルダIDを`.env`ファイルに追加します。
   `--email`パラメータを指定すると、作成されたフォルダが指定したメールアドレスと共有されます。
   これにより、サービスアカウントが所有するフォルダにアクセスできるようになります。

### 5. LINE APIの設定
1. LINE Developersでプロバイダーとチャネルを作成
2. Messaging APIとLIFFを設定
3. Webhook URLを設定
4. チャネルアクセストークンとチャネルシークレットを`.env`ファイルに設定

### 6. ローカル開発サーバーの起動
```bash
python app.py
```

### 7. Vercelへのデプロイ
```bash
vercel
```

## 使い方

### 管理者向け
1. 管理画面にアクセスし、こども食堂を登録
2. 質問と回答選択肢を設定
3. シールの色の意味を設定
4. アンケート用紙テンプレートを印刷して参加者に配布

### ユーザー向け
1. LINE公式アカウントを友だち追加
2. 「アンケート」と送信してLIFFアプリを起動
3. 初回利用時はユーザー登録を実施
4. カメラを起動し、アンケート用紙を撮影
5. 自動集計結果を確認

### 開発者向け
1. テスト画像の生成:
   ```bash
   python generate_test_image.py --output test_image.jpg
   ```
   このスクリプトはシールが貼られたアンケート用紙のテスト画像を生成します。物理的なアンケート用紙を作成せずに画像処理機能をテストするのに便利です。
   
   カスタムのシール配置を指定することもできます:
   ```bash
   python generate_test_image.py --output test_image.jpg --stickers "UL:red=3,green=2,blue=1,yellow=0;UR:red=1,green=4,blue=2,yellow=1;LL:red=0,green=1,blue=3,yellow=2;LR:red=2,green=0,blue=1,yellow=3"
   ```

2. 画像処理機能のテスト:
   ```bash
   python test_image_processing.py --image_path test_image.jpg
   ```
   このスクリプトは指定された画像を処理し、結果を表示します。LINE LIFFアプリを使わずに画像処理機能をテストするのに便利です。

3. LINE Webhook機能のテスト:
   ```bash
   python test_line_webhook.py --message "アンケート" --user_id "test_user_id"
   ```
   このスクリプトはLINE Webhookイベントをシミュレートし、ローカルのFlaskアプリケーションに送信します。LINE公式アカウントからのメッセージ受信をテストするのに便利です。

### アンケート用紙テンプレート
アンケート用紙のテンプレートは以下のURLでアクセスできます：
```
https://your-app-url.vercel.app/survey-template
```

ローカル開発環境では以下のURLでアクセスできます：
```
http://localhost:5000/survey-template
```

このテンプレートはA4用紙（横向き）に最適化されており、印刷ボタンをクリックすることで印刷できます。

## ディレクトリ構造

```
kodomo-shokudo-survey/
├── .env                    # 環境変数
├── .env.template           # 環境変数テンプレート
├── requirements.txt        # Pythonパッケージ依存関係
├── app.py                  # Flaskアプリケーションのエントリーポイント
├── vercel.json             # Vercel設定ファイル
├── static/                 # 静的ファイル
│   ├── js/                 # JavaScriptファイル
│   ├── css/                # CSSファイル
│   └── img/                # 画像ファイル
├── templates/              # HTMLテンプレート
├── services/               # サービスレイヤー
├── api/                    # Vercelのサーバーレス関数
└── README.md               # このファイル
```

## ライセンス

MIT

## 謝辞

このプロジェクトは以下のオープンソースライブラリを使用しています：
- Flask
- OpenCV
- LINE SDK
- Google API Client Library
- Bootstrap
