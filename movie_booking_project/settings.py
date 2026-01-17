"""
Django settings for movie_booking_project project.
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local Apps
    'users',
    'movies',
    'theatres',
    'bookings',
    'food',
    'payments',
    'utils',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'movie_booking_project.urls'

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
                'django.template.context_processors.media',
                'movie_booking_project.settings.settings_context',
            ],
        },
    },
]


def settings_context(request):
    """Context processor to expose Django settings to templates"""
    from django.conf import settings
    return {
        'settings': settings,
    }

WSGI_APPLICATION = 'movie_booking_project.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
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
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'movies:movie_list'
LOGOUT_REDIRECT_URL = 'users:login'

# Session settings
SESSION_COOKIE_AGE = 86400  # 1 day
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Email configuration - Gmail SMTP Backend
# Check if app password is properly configured
_email_password = config('EMAIL_HOST_PASSWORD', default='').strip()

# Use file backend for testing/development if no real password is set
if _email_password and not _email_password.startswith('paste_'):
    # Real password is set, use SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='sandeshgend101@gmail.com')
    EMAIL_HOST_PASSWORD = _email_password
    DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='sandeshgend101@gmail.com')
else:
    # No password or placeholder detected - use file backend for testing
    # Emails will be saved to a file instead of being sent
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
    DEFAULT_FROM_EMAIL = config('EMAIL_HOST_USER', default='sandeshgend101@gmail.com')

# Contact Information
CONTACT_EMAIL = config('CONTACT_EMAIL', default='sandeshgend101@gmail.com')
CONTACT_PHONE = config('CONTACT_PHONE', default='+91 7821884694')
CONTACT_ADDRESS = config('CONTACT_ADDRESS', default='ITP, Pune, Maharashtra, India')
CONTACT_HOURS = config('CONTACT_HOURS', default='10 AM - 10 PM (Mon-Sun)')

# Razorpay API keys - Load from environment, fallback to test keys
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='rzp_test_S1fft0Wgnv1ulI')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='KuicTTUt04XID2bNu1j5aeJj')

# Razorpay simulation mode (set to False to use real API)
# When True, payments are simulated locally without making API calls
# When False, real Razorpay API is called (requires valid API keys and internet)
RAZORPAY_FORCE_SIMULATION = config('RAZORPAY_FORCE_SIMULATION', default=False, cast=bool)

# Validate Razorpay configuration
if not RAZORPAY_KEY_ID.startswith('rzp_test_') and not RAZORPAY_KEY_ID.startswith('rzp_live_'):
    raise ValueError("Invalid RAZORPAY_KEY_ID: Must start with 'rzp_test_' or 'rzp_live_'")

if not RAZORPAY_KEY_SECRET:
    raise ValueError("Invalid RAZORPAY_KEY_SECRET: Cannot be empty")

# For testing Razorpay integration
if DEBUG:
    RAZORPAY_KEY_ID = 'rzp_test_S1fft0Wgnv1ulI'
    RAZORPAY_KEY_SECRET = 'KuicTTUt04XID2bNu1j5aeJj'