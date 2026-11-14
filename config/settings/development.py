from .base import *

DEBUG = True

# In local development without Postgres running, fallback gracefully to SQLite
# unless DATABASE_URL is explicitly set and reachable.
if 'DATABASES' not in globals() or not DATABASES.get('default'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

