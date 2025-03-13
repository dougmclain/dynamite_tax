"""
Django settings for HOA_tax project.
"""

from pathlib import Path
import os
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()
# Explicitly load the .env file from the project root (i.e., the directory containing manage.py)
env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJANGO_DEBUG', False)
IS_PRODUCTION = not DEBUG

ALLOWED_HOSTS = ['dynamite-tax.onrender.com', 'localhost', '127.0.0.1']
if IS_PRODUCTION and 'RENDER_EXTERNAL_HOSTNAME' in os.environ:
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])

# Application definition
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_bootstrap5',
    'crispy_forms',
    'tax_form',
    'storages',  # Add django-storages
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'tax_form.middleware.AssociationSessionMiddleware',  # <-- Moved after SessionMiddleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HOA_tax.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

WSGI_APPLICATION = 'HOA_tax.wsgi.application'

# Database configuration
import dj_database_url

# Check if we're running in production or development
if IS_PRODUCTION:
    # Production database (from DATABASE_URL env var)
    DATABASES = {
        'default': dj_database_url.parse(env('DATABASE_URL'))
    }
else:
    # Development database (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    # Optionally, you can override with DATABASE_URL if provided but only if explicitly requested
    if env('USE_PRODUCTION_DB', default=False):
        DATABASES['default'] = dj_database_url.parse(env('DATABASE_URL'))

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Azure Storage Configuration
USE_AZURE_STORAGE = env.bool('USE_AZURE_STORAGE', IS_PRODUCTION)  # Default to using Azure in production

if USE_AZURE_STORAGE:
    # Azure Storage Settings
    AZURE_ACCOUNT_NAME = env('AZURE_ACCOUNT_NAME', default='dynamitetax')
    AZURE_ACCOUNT_KEY = env('AZURE_ACCOUNT_KEY', default='')
    AZURE_CONTAINER = env('AZURE_CONTAINER', default='media')
    
    # Configure the default storage
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    
    # Media files URL (this will be the base URL for accessing your files)
    MEDIA_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/'
    
    # Optional: Set custom domain if you have one
    # AZURE_CUSTOM_DOMAIN = 'cdn.yourdomain.com'
    
    # Optional: Set this to True if using CDN with HTTPS
    AZURE_SSL = True
    
    # Optional: Set default ACL for new files
    AZURE_DEFAULT_CONTENT_TYPE = 'application/octet-stream'
    
    # Create the temp_pdfs directory locally (still needed for temporary PDF generation)
    PDF_TEMPLATE_DIR = Path('/opt/render/project/src/tax_form/pdf_templates') if IS_PRODUCTION else BASE_DIR / 'tax_form' / 'pdf_templates'
    PDF_TEMP_DIR = Path('/opt/render/project/src/tax_form/temp_pdfs') if IS_PRODUCTION else BASE_DIR / 'tax_form' / 'temp_pdfs'
    os.makedirs(PDF_TEMP_DIR, exist_ok=True)
else:
    # Local media configuration
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media_files')
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    
    # Create media directories if they don't exist
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'completed_tax_returns'), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'extensions'), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'engagement_letters'), exist_ok=True)
    os.makedirs(os.path.join(MEDIA_ROOT, 'signed_engagement_letters'), exist_ok=True)
    
    # PDF paths - separate from media
    if DEBUG:
        PDF_BASE = Path('/Users/Doug/Library/Mobile Documents/com~apple~CloudDocs/Dynamite Software Development/Dynamite Tax ')
        PDF_TEMPLATE_DIR = PDF_BASE / 'tax_form' / 'pdf_templates'
        PDF_TEMP_DIR = PDF_BASE / 'temp_pdfs'
        # Create temp directory locally
        os.makedirs(PDF_TEMP_DIR, exist_ok=True)
    else:
        PDF_TEMPLATE_DIR = BASE_DIR / 'tax_form' / 'pdf_templates'
        PDF_TEMP_DIR = BASE_DIR / 'tax_form' / 'temp_pdfs'
        os.makedirs(PDF_TEMP_DIR, exist_ok=True)

# Security settings for production
if IS_PRODUCTION:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    CSRF_TRUSTED_ORIGINS = ['https://dynamite-tax.onrender.com']

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'tax_form': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'storages': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if IS_PRODUCTION else 'DEBUG',
    },
}

# Session settings
SESSION_COOKIE_AGE = 86400  # Session lasts for 24 hours (in seconds)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Session survives browser close

LOGIN_URL = '/admin/login/'