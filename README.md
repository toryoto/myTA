## 環境構築

### 手順

1. **リポジトリのクローン**
```bash
git clone <repository-url>
cd diary-app
```

2. **環境変数の設定**
```bash
# .envファイルを作成
cp .env.example .env

3. **アプリケーションの起動**
```bash
# コンテナのビルドと起動
docker-compose up --build

# 初回のみ：データベースのセットアップ
docker-compose exec web uv run python manage.py migrate

# 管理ユーザーの作成（オプション）
docker-compose exec web uv run python manage.py createsuperuser
```

4. **アクセス確認**
- アプリケーション: http://localhost:8000
- 管理画面: http://localhost:8000/admin

## 開発

### 日常的な起動
```bash
docker-compose up
```

### CSS変更時
```bash
# Tailwind CSSの再ビルド
docker-compose exec web bash -c "cd theme/static_src && npm run build"
```

### データベースリセット
```bash
docker-compose down -v
docker-compose up --build
```

### CSSが反映されない
```bash
docker-compose exec web bash -c "cd theme/static_src && npm run build"
```

### データベースエラー
```bash
docker-compose exec web uv run python manage.py migrate
```