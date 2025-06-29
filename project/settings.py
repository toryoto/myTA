import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.core.management.utils import get_random_secret_key

load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret Manager 用の関数
def get_secret(secret_id):
    """Secret Manager から機密情報を取得"""
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = "django-pra"
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # 開発環境やテスト時のフォールバック
        return os.getenv(secret_id, "")

# 環境判定
IS_CLOUD_RUN = os.getenv('K_SERVICE') is not None
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

# Cloud Run での実行時は production に設定
if IS_CLOUD_RUN:
    ENVIRONMENT = "production"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
BUILD_COMMANDS = ['collectstatic', 'tailwind']
is_build_command = any(cmd in sys.argv for cmd in BUILD_COMMANDS)

if not SECRET_KEY:
    if IS_CLOUD_RUN:
        # Cloud Run では Secret Manager から取得
        SECRET_KEY = get_secret('django-secret-key')
    elif is_build_command:
        # ビルド時は一時的なキーを生成
        SECRET_KEY = get_random_secret_key()
        print("INFO: Using temporary SECRET_KEY for build command")
    elif ENVIRONMENT == "production":
        # 本番環境でSECRET_KEYが設定されていない場合はエラー
        raise ValueError("DJANGO_SECRET_KEY environment variable is required in production")
    else:
        # 開発環境では一時的なキーを生成
        SECRET_KEY = get_random_secret_key()
        print("WARNING: Using temporary SECRET_KEY. Set DJANGO_SECRET_KEY environment variable.")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

# Cloud Run では DEBUG を False に強制
if IS_CLOUD_RUN:
    DEBUG = False

ALLOWED_HOSTS = []
if IS_CLOUD_RUN:
    ALLOWED_HOSTS = ['*']  # 実際のドメインに制限することを推奨

# Application definition
INSTALLED_APPS = [
    "diary.apps.DiaryConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "widget_tweaks",
    "storages",
    "tailwind",
    "theme",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# Database
if IS_CLOUD_RUN:
    # Cloud Run での Cloud SQL 接続
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": get_secret('db-name'),
            "USER": get_secret('db-user'),
            "PASSWORD": get_secret('db-password'),
            "HOST": f'/cloudsql/{get_secret("db-connection-name")}',
            "PORT": "5432",
        }
    }
elif ENVIRONMENT == "production":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME"),
            "USER": os.environ.get("DB_USER"),
            "PASSWORD": os.environ.get("DB_PASSWORD"),
            "HOST": os.environ.get("DB_HOST"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
elif ENVIRONMENT == "docker":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "django_diary"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "test1234"),
            "HOST": os.environ.get("POSTGRES_HOST", "db"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# File storage settings
if DEBUG and not IS_CLOUD_RUN:
    # 開発環境ではローカルに画像を保存
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"
else:
    # 本番環境（Cloud Run含む）でのみGoogle Cloud Storageを使用
    DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
    GS_BUCKET_NAME = "django_diary_bucket"
    GS_PROJECT_ID = "django-pra"

    gcp_key_path = BASE_DIR / "gcp_key.json"
    if gcp_key_path.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(gcp_key_path)
        GS_CREDENTIALS = None

# Cloud Run でのセキュリティ設定
if IS_CLOUD_RUN:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/diary"
LOGOUT_REDIRECT_URL = "/"

TAILWIND_APP_NAME = "theme"