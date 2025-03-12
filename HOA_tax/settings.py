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
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'tax_form.middleware.AssociationSessionMiddleware',  # 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
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
DATABASES = {
    'default': dj_database_url.parse(env('DATABASE_URL'))
}

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

# Media and PDF paths - using the correct Render paths
if DEBUG:
    # Local development settings
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    PDF_TEMPLATE_DIR = Path('/Users/Doug/Library/Mobile Documents/com~apple~CloudDocs/Dynamite Software Development/Dynamite Tax/tax_form/pdf_templates')
    PDF_TEMP_DIR = Path('/Users/Doug/Library/Mobile Documents/com~apple~CloudDocs/Dynamite Software Development/Dynamite Tax/temp_pdfs')
else:
    # Production settings - use Render's disk mounting system
    MEDIA_ROOT = '/var/lib/render/disk'
    PDF_TEMPLATE_DIR = Path('/var/lib/render/disk/pdf_templates')
    PDF_TEMP_DIR = Path('/var/lib/render/disk/temp_pdfs')

# Media files
MEDIA_URL = '/media/'
if IS_PRODUCTION:
    # Use Render's writable disk mounting path
    MEDIA_ROOT = '/var/lib/render/disk/media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
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