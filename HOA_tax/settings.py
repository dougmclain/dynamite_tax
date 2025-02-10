"""
Django settings for HOA_tax project.
"""

from pathlib import Path
import os
import environ

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-9cu%k8-q=ej+lfa-hf_)saqez!-l$8@sx#pjsw@c!nu8yesf0q')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)
IS_PRODUCTION = not DEBUG

ALLOWED_HOSTS = ['hoa-tax-help.onrender.com', 'localhost', '127.0.0.1']
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
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add whitenoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HOA_tax.urls'
WSGI_APPLICATION = 'HOA_tax.wsgi.application'

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

# Database configuration
# Local SQLite database - commented out for now but keep for later data transfer
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""




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

# Media files
MEDIA_URL = '/media/'
if IS_PRODUCTION:
    MEDIA_ROOT = '/tmp/media'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# PDF Settings
if IS_PRODUCTION:
    PDF_TEMPLATE_DIR = Path('/opt/render/project/src/tax_form/pdf_templates')
    PDF_TEMP_DIR = Path('/tmp/temp_pdfs')
else:
    PDF_BASE = Path('/Users/Doug/Library/Mobile Documents/com~apple~CloudDocs/Dynamite Software Development/Dynamite Tax ')
    PDF_TEMPLATE_DIR = PDF_BASE / 'tax_form' / 'pdf_templates'
    PDF_TEMP_DIR = PDF_BASE / 'temp_pdfs'

# Create temp directory only (template directory will be handled in build script)
os.makedirs(PDF_TEMP_DIR, exist_ok=True)

# Copy templates in production during startup
if IS_PRODUCTION:
    import shutil
    source_templates = Path(BASE_DIR) / 'tax_form' / 'pdf_templates'
    if source_templates.exists():
        os.makedirs(PDF_TEMPLATE_DIR, exist_ok=True)
        for template_file in source_templates.glob('*.pdf'):
            shutil.copy2(template_file, PDF_TEMPLATE_DIR / template_file.name)

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
    CSRF_TRUSTED_ORIGINS = ['https://hoa-tax-help.onrender.com']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO' if IS_PRODUCTION else 'DEBUG',
    },
}