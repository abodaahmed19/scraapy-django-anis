from pathlib import Path
import os
from decimal import Decimal, ROUND_HALF_UP
from decouple import config
from django.core.exceptions import ImproperlyConfigured
from datetime import timedelta
from cryptography.hazmat.primitives import hashes
import hashlib

# Feature flags
DISABLE_REGISTRATION = False

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-à-changer')
if not SECRET_KEY:
    raise ImproperlyConfigured("Le paramètre SECRET_KEY ne peut pas être vide.")

# Determine environment stage
STAGE = os.environ.get('STAGE', 'development').lower()
if STAGE == 'development':
    DEBUG = True
    TESTING = True
elif STAGE == 'testing':
    DEBUG = True
    TESTING = True
else:  # production
    DEBUG = False
    TESTING = False

SITE_NAME = os.environ.get('SITE_NAME', 'Scraapy')
DOMAIN = os.environ.get('DOMAIN', '127.0.0.1:8000')  # format host:port
APP_URL = os.environ.get('APP_URL', 'http://' + DOMAIN)
# only used on production to set social redirect urls and CORS allowed origins
FRONTEND_DOMAIN = os.environ.get(
    'FRONTEND_DOMAIN', 'http://' + DOMAIN.split(':')[0] + ':5173'
)

# Hosts configuration
if STAGE == 'development':
    ALLOWED_HOSTS =  [
    '38.242.237.116',
    'localhost',
    '127.0.0.1',
    'api.scraapy.sa', 
    'vmi2584358.contaboserver.net', 
]
else:
     ALLOWED_HOSTS = [DOMAIN.split(':')[0], 'api.scraapy.sa']

# Ensure ALLOWED_HOSTS is set in production
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be set when DEBUG is False')

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://10.0.2.2:8000',
    APP_URL,
    'https://api.scraapy.sa',
]

# Application definition
INSTALLED_APPS = [
    'corsheaders',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'knox',
    'sms',
    'djoser',
    
    'social_django',
    'phonenumber_field',
    'main',
    'pms',
    'inventory',
    'bms',
    'dms',
    'otp',
    'driver',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scraapy.urls'

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

WSGI_APPLICATION = 'scraapy.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'scraapydb',  # <- mets le bon nom ici
        'USER': 'anis',
        'PASSWORD': 'Gouadria@1982',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}







KNOX_TOKEN_TTL = timedelta(hours=1)

APPEND_SLASH = False

# SMS settings
JAWALBSMS_USER = config('JAWALBSMS_USER')
JAWALBSMS_PASS = config('JAWALBSMS_PASS')
JAWALBSMS_SENDER = config('JAWALBSMS_SENDER')
JAWALBSMS_APIURL = config('JAWALBSMS_APIURL')

# Cache configuration
redis_host = os.environ.get('REDIS_HOST', 'localhost')
if redis_host not in ['localhost', '10.0.2.2']:
    redis_host = 'localhost'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{redis_host}:6379/0',
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

# Custom user model
AUTH_USER_MODEL = 'pms.User'

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'knox.auth.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
    'anon': '1000/minute',
    'user': '2000/minute',
    'verify_otp': '10/minute',
},

}

JWT_SECRET_KEY = "rZDj7H8tyVkNpLfI3o1FJQw-E9aKR_5W2BncHyqlycQ"

# Social auth redirect URLs
if TESTING or DEBUG:
    SOCIAL_REDIRECT_URLS = [
        'http://workstation1.hq.uzdsolutions.com:5173/auth/google/callback/',
        'http://workstation2.hq.uzdsolutions.com:5173/auth/google/callback/',
        'http://workstation3.hq.uzdsolutions.com:5173/auth/google/callback/',
        'http://workstation4.hq.uzdsolutions.com:5173/auth/google/callback/',
        'http://127.0.0.1:5173/auth/google/callback/',
    ]
else:
    SOCIAL_REDIRECT_URLS = [FRONTEND_DOMAIN + '/auth/google/callback/']

#Djoser configuration
DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': False,
    'SERIALIZERS': {
        'user': 'pms.serializers.UserSerializer',
        'current_user': 'pms.serializers.UserSerializer',
    },
    'PERMISSIONS': {
        'user': ['rest_framework.permissions.IsAuthenticated'],
    }
}

# Cette condition doit être propre et en anglais uniquement
if DISABLE_REGISTRATION:
    DJOSER['PERMISSIONS']['user_create'] = ['rest_framework.permissions.IsAdminUser']

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

# Rest Knox settings
REST_KNOX = {
    'USER_SERIALIZER': 'pms.serializers.UserSerializer',
    'AUTO_REFRESH': True,
    'MIN_REFRESH_INTERVAL': 120,
}

# OAuth2 credentials
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
CORS_ALLOW_CREDENTIALS = True

# CORS configuration
if DEBUG or TESTING:
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r'^http://localhost:\d+$',
        r'^http://127\.0\.0\.1:\d+$',
        r'^http://10\.0\.2\.2:\d+$',
        r'^http://workstation\d+\.hq\.uzdsolutions\.com:\d+$',
        r'^http://tauri.localhost',
    ]
else:
   CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://38.242.237.116',
    'https://scraapy.sa',

]

CORS_ALLOW_ALL_ORIGINS = True

SESSION_COOKIE_SAMESITE = 'Lax'

# Password validation
#AUTH_PASSWORD_VALIDATORS = [
   # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    #{'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
#]

# Email configuration
#if DEBUG:
    #EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#else:
    #EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = os.environ.get('EMAIL_HOST', 'box.uzdsolutions.com')
#EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', False)
#EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', True)
#EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 465))
#EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
#EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
#DEFAULT_FROM_EMAIL = 'maint@uzdsolutions.com'

EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = 'smtp.zoho.sa'
EMAIL_PORT         = 587
EMAIL_USE_SSL      = False   # désactivé
EMAIL_USE_TLS      = True    # STARTTLS
EMAIL_HOST_USER    = 'scraapy@zohomail.sa'
EMAIL_HOST_PASSWORD= '5WXkg6fUv6L3'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True



# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Riyadh'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
PROTECTED_MEDIA_ROOT = BASE_DIR / 'protected_media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# VAT settings
VAT = Decimal('0.15')
# Moyasar configuration
MOYASAR_API_KEY = os.environ.get('MOYASAR_API_KEY', '')
MOYASAR_CALLBACK_URL = os.environ.get('MOYASAR_CALLBACK_URL', FRONTEND_DOMAIN + '/payment/callback/')


LOG_DIR = BASE_DIR / 'logs' / 'django'
os.makedirs(LOG_DIR, exist_ok=True)  # Crée le dossier s'il n'existe pas

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'app': {
            'format': '%(asctime)s [%(levelname)-8s] (%(module)s.%(funcName)s) %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',  # Passer en DEBUG pour tout logger lié au fichier
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'django.log',
            'formatter': 'app',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        # Logger pour les requêtes SQL
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',  # Capture les requêtes SQL
            'propagate': False,
        },
    }
}
