import os
import sys
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Automatically load environment variables from backend/.env or root .env
def _load_env_file(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, _, v = line.partition('=')
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v

_load_env_file(BASE_DIR / '.env')
_load_env_file(BASE_DIR.parent / '.env')

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-recruitment-dev-key-change-in-prod-xyz123')

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'channels',
    'storages',


    # Local apps
    'apps.accounts',
    'apps.companies',
    'apps.jobs',
    'apps.applications',
    'apps.notifications',
    'apps.common',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Supabase Credentials (Only SUPABASE_URL and SUPABASE_KEY needed for Supabase connection!)
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = (
    os.environ.get('SUPABASE_KEY')
    or os.environ.get('SUPABASE_ANON_KEY')
    or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    or ''
)
SUPABASE_BUCKET_NAME = os.environ.get('SUPABASE_BUCKET_NAME', 'hirepulse')

# Database configuration (Supabase PostgreSQL / Local PostgreSQL / SQLite fallback)
DATABASE_URL = os.environ.get('SUPABASE_DB_URL') or os.environ.get('DATABASE_URL')
SUPABASE_DB_PASSWORD = os.environ.get('SUPABASE_DB_PASSWORD')

if DATABASE_URL and (DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')):
    from urllib.parse import urlparse, parse_qs, unquote
    parsed_db = urlparse(DATABASE_URL)
    query_params = parse_qs(parsed_db.query)

    is_supabase = (
        'supabase.co' in (parsed_db.hostname or '') or
        'supabase.com' in (parsed_db.hostname or '') or
        'pooler.supabase' in (parsed_db.hostname or '')
    )
    is_pooler = 'pooler.supabase' in (parsed_db.hostname or '') or (parsed_db.port == 6543)

    # Supabase strictly requires SSL
    sslmode = query_params.get('sslmode', ['require' if is_supabase else 'prefer'])[0]

    db_options = {}
    if sslmode:
        db_options['sslmode'] = sslmode

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': unquote(parsed_db.path.lstrip('/') or 'postgres'),
            'USER': unquote(parsed_db.username or 'postgres'),
            'PASSWORD': unquote(parsed_db.password or ''),
            'HOST': parsed_db.hostname or 'localhost',
            'PORT': parsed_db.port or 5432,
            'OPTIONS': db_options,
            'CONN_MAX_AGE': 0,  # PgBouncer handles connection pooling; persistent connections must be disabled
            'DISABLE_SERVER_SIDE_CURSORS': is_pooler,  # Required for PgBouncer transaction mode
        }
    }
elif SUPABASE_URL and SUPABASE_DB_PASSWORD:
    # Auto-configured directly using SUPABASE_URL and database password!
    from urllib.parse import urlparse
    parsed_supa = urlparse(SUPABASE_URL)
    project_ref = parsed_supa.hostname.split('.')[0] if parsed_supa.hostname else ''
    db_host = os.environ.get('SUPABASE_DB_HOST', f"db.{project_ref}.supabase.co")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'postgres',
            'USER': f'postgres.{project_ref}' if 'pooler' in db_host else 'postgres',
            'PASSWORD': SUPABASE_DB_PASSWORD,
            'HOST': db_host,
            'PORT': int(os.environ.get('SUPABASE_DB_PORT', '5432')),
            'OPTIONS': {
                'sslmode': 'require',
            },
            'CONN_MAX_AGE': 0,
            'DISABLE_SERVER_SIDE_CURSORS': 'pooler' in db_host,
        }
    }
elif os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST'):
    db_host = os.environ.get('POSTGRES_HOST') or os.environ.get('DB_HOST')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'recruitment_db'),
            'USER': os.environ.get('POSTGRES_USER', 'recruiter'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': db_host,
            'PORT': int(os.environ.get('POSTGRES_PORT', '5432')),
            'OPTIONS': {
                'sslmode': 'prefer',
            },
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '0')),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Use fast SQLite in-memory database when running unit tests (avoids remote PgBouncer CREATE DATABASE blocks)
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Storage Configuration
# Priority 1: Supabase Storage (Only SUPABASE_URL and SUPABASE_KEY needed!)
# Priority 2: AWS S3 (when AWS_STORAGE_BUCKET_NAME is configured)
# Priority 3: Local FileSystem (default zero-config fallback for tests & local dev)
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = int(os.environ.get('AWS_QUERYSTRING_EXPIRE', '3600'))

USE_SUPABASE_STORAGE = bool(SUPABASE_URL and SUPABASE_KEY)
USE_AWS_S3 = bool(
    AWS_STORAGE_BUCKET_NAME and
    (AWS_ACCESS_KEY_ID or os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') or os.environ.get('AWS_ROLE_ARN'))
)

if USE_SUPABASE_STORAGE:
    STORAGES = {
        'default': {
            'BACKEND': 'apps.common.storage.SupabaseStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
elif USE_AWS_S3:
    STORAGES = {
        'default': {
            'BACKEND': 'apps.common.storage.MediaStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
else:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

if 'test' in sys.argv:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.InMemoryStorage',
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'auth': '20/minute',
        'apply': '30/minute',
        'upload': '30/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'EXCEPTION_HANDLER': 'apps.common.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

if 'test' in sys.argv:
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'anon': '10000/day',
        'user': '10000/day',
        'auth': '10000/minute',
        'apply': '10000/minute',
        'upload': '10000/minute',
    }

# SimpleJWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# CORS Settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:80'
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# JWT HttpOnly Cookie Settings (Protected from JavaScript access)
AUTH_COOKIE_REFRESH = 'refresh_token'
AUTH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days
AUTH_COOKIE_SECURE = not DEBUG  # True in production HTTPS, False in local HTTP
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = '/'
AUTH_COOKIE_SAMESITE = 'Lax'

# Spectacular API Docs
SPECTACULAR_SETTINGS = {
    'TITLE': 'Job Recruitment Platform API',
    'DESCRIPTION': 'Enterprise Recruitment Management Platform API with JWT Auth, Role-based Access, and Real-time Notifications.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'ENUM_NAME_OVERRIDES': {
        'JobStatusEnum': 'apps.jobs.models.JobStatus',
        'ApplicationStatusEnum': 'apps.applications.models.ApplicationStatus',
    },
}

# Channels Channel Layer (Redis if available, InMemory fallback)
REDIS_URL = os.environ.get('REDIS_URL')
use_redis = False

if REDIS_URL:
    use_redis = True
    # If in local development and configured to localhost, verify if Redis port is listening
    if DEBUG and ('localhost' in REDIS_URL or '127.0.0.1' in REDIS_URL):
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            s.connect(('127.0.0.1', 6379))
            s.close()
        except Exception:
            use_redis = False

if use_redis:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    # Zero-setup fallback for development without running Redis locally
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# File Upload Constraints
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_RESUME_EXTENSIONS = ['.pdf', '.doc', '.docx']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

