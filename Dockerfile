# Python 3.12の軽量版イメージを使用
FROM python:3.12-slim

# コンテナ内の作業ディレクトリを /app に設定
WORKDIR /app

# 依存ライブラリリストをコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 残りの全ファイル（main.py, engine.py, dataフォルダなど）をコピー
COPY . .

# サーバーが外部からアクセスを受け付けるためのポート設定
ENV PORT=8080

# アプリケーションを起動
CMD ["python", "main.py"]