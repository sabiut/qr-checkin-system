import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
print(f"Loaded .env file from {os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')}")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Temporarily set to True for debugging

ALLOWED_HOSTS = ['*']  # Adjust this for production

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'channels',  # Enabled for WebSocket support
    
    # Local apps
    'events',
    'invitations',
    'attendance',
    'users',
    'gamification',
    'feedback_system',
    'networking',
    'communication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qrcheckin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'qrcheckin', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'qrcheckin.context_processors.admin_stats',
            ],
        },
    },
]

WSGI_APPLICATION = 'qrcheckin.wsgi.application'
ASGI_APPLICATION = 'qrcheckin.asgi.application'  # Enabled for WebSocket support

# Channel layer configuration for WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Add a renderer for browsable API which is helpful for debugging
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# CORS settings - control which domains can make API requests
# Type: List[str] - List of allowed origins for cross-origin requests
CORS_ALLOWED_ORIGINS = [
    # Production domains
    "https://eventqr.app",      # Primary production domain
    "https://www.eventqr.app",  # WWW subdomain for production
] + ([
    # Development domains - only included in DEBUG mode
    "http://localhost:3000",    # Frontend development server (React/Vite)
    "http://localhost:5173",    # Alternative frontend dev server port
    "http://frontend:3000",     # Docker development frontend service
    "http://127.0.0.1:3000",    # Local development (IP-based)
    "http://127.0.0.1:5173",    # Local development (IP-based, alt port)
] if DEBUG else [])

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = True  # Allow cookies/auth headers in CORS requests

# CSRF settings - trusted origins for secure form submissions
# Type: List[str] - Only origins listed here can submit forms to Django views with CSRF protection
CSRF_TRUSTED_ORIGINS = [
    # Production domains - main application domains
    "https://eventqr.app",      # Primary production domain
    "https://www.eventqr.app",  # WWW subdomain for production
] + ([
    # Development domains - only included in DEBUG mode
    "http://localhost:3000",    # Frontend development server (React/Vite)
    "http://localhost:5173",    # Alternative frontend dev server port
    "http://127.0.0.1:3000",    # Local development (IP-based)
    "http://127.0.0.1:5173",    # Local development (IP-based, alt port)
] if DEBUG else [])

# Offline mode settings
OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'False') == 'True'

# Email settings
# Use environment variable to control email backend instead of DEBUG mode
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# For development debugging - uncomment to see emails in console instead:
# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'sum.abiutaws@gmail.com')

# Frontend URL for email links and guest responses
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

# Configure email logging (useful for debugging)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'invitations': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Base URL for absolute URLs in templates (used for tickets)
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')