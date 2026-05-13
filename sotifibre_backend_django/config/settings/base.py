"""
Base settings for SUPERVISION OLT project.
"""
import os
from pathlib import Path
from datetime import timedelta
from celery.schedules import crontab
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY", default="django-insecure-ii!k95t4_$!767b+geh5bc$m9@v!fih^!cz7kaje-mon@1qf*q")
DEBUG = env("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition
DJANGO_APPS = [
    "jazzmin",  # must be before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'import_export',
    'django_extensions',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
]

LOCAL_APPS = [
    # Core app (must be first)
    'apps.core',
    
    # User management
    'apps.users',
    
    # Custom Apps - Power BI Backend
    'apps.data_sources',
    'apps.etl_engine',
    'apps.data_warehouse',  
    'apps.star_schema',
    'apps.visualizations',
    'apps.notifications',
    'apps.ml_analytics',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATABASES = {
    # Core, Users, Data Sources, ETL Engine
    "default": {
        "ENGINE": env("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": env("DB_NAME", default="supervisionolt_db"),
        "USER": env("DB_USER", default="supervisionolt_admin"),
        "PASSWORD": env("DB_PASSWORD", default="123456"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    },
}

# Routeur pour diriger les modèles data_warehouse vers la bonne base
""" DATABASE_ROUTERS = [
    'apps.data_warehouse.routers.DataWarehouseRouter',
]
 """
# Cache avec Redis
# config/settings/base.py

""" # Cache avec Redis - VERSION CORRIGÉE
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            # 'CLIENT_CLASS' n'est PAS supporté - À SUPPRIMER
        },
        'KEY_PREFIX': 'iotshield',
        'TIMEOUT': 300,  # 5 minutes
    },
    
    'nvd': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/2'),
        'KEY_PREFIX': 'nvd',
        'TIMEOUT': 86400,  # 24 heures
    },
    
    'scans': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/3'),
        'KEY_PREFIX': 'scans',
        'TIMEOUT': 3600,  # 1 heure
    },
} """

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.users.authentication.EmailAuthBackend',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── REST Framework ───────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "10/minute",
        "scan": "50/day",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "ALLOWED_VERSIONS": ['v1', 'v2'],
    "DEFAULT_VERSION": 'v1',
}

# ─── JWT ──────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("ACCESS_TOKEN_LIFETIME_MINUTES", default=60)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainSerializer',
}

# ─── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# CHANNELS CONFIGURATION (WebSocket)
# ============================================================================

# Vérifier que CHANNEL_LAYERS est correctement configuré
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Si Redis n'est pas disponible, utiliser le backend InMemory pour le développement
if DEBUG:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ============================================================================
# EMAIL CONFIGURATION
# ============================================================================

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@sotifibre.com')

# Anymail pour les services email avancés (SendGrid, Mailgun, etc.)
ANYMAIL = {
    "SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY", ""),
}
EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"  # Optionnel

# settings.py
# ============================================================================
# SMS CONFIGURATION (Twilio)
# ============================================================================

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# ============================================================================
# SLACK & TEAMS CONFIGURATION
# ============================================================================

SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', '')

# ============================================================================
# CELERY CONFIGURATION
# ============================================================================

# Broker Redis
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django-db')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 20 * 60

# Celery Beat pour les tâches planifiées
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Configuration Celery Beat pour les notifications
CELERY_BEAT_SCHEDULE = {
    'check-alert-rules-every-minute': {
        'task': 'apps.notifications.tasks.check_alert_rules',
        'schedule': 60.0,  # Toutes les minutes
    },
    'send-pending-notifications-every-30-seconds': {
        'task': 'apps.notifications.tasks.send_pending_notifications',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
    'clean-old-notifications-daily': {
        'task': 'apps.notifications.tasks.clean_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # 2h du matin
    },
}

# ─── API Docs ─────────────────────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "SOTIFibre Platform API",
    "DESCRIPTION": "IOT Sécurité Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}

# ─── Jazzmin Admin Theme ──────────────────────────────────────────────────────
# Jazzmin
from .jazzmin_settings import *

# ─── ML Models Configuration ──────────────────────────────────────────────────
ML_MODELS_PATH = BASE_DIR / 'data' / 'ml_models'
DEVICE_CLASSIFIER_PATH = ML_MODELS_PATH / 'device_classifier.pkl'
RISK_PREDICTOR_PATH = ML_MODELS_PATH / 'risk_predictor.pkl'
ANOMALY_DETECTOR_PATH = ML_MODELS_PATH / 'anomaly_detector.pkl'

# ─── File Uploads ─────────────────────────────────────────────────────────────
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_PERMISSIONS = 0o644

# ─── Security Headers ─────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# ─── Rate Limiting ────────────────────────────────────────────────────────────
LOGIN_RATE_LIMIT = env("LOGIN_RATE_LIMIT", default="10/m")

# ─── Test Runner ──────────────────────────────────────────────────────────────
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_NON_SERIALIZED_APPS = ['django.contrib.contenttypes', 'django.contrib.auth']

# ─── Session Configuration ────────────────────────────────────────────────────
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 heures
SESSION_SAVE_EVERY_REQUEST = True

# ─── CSRF Trusted Origins ─────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
])

# ─── Internal IPs ─────────────────────────────────────────────────────────────
INTERNAL_IPS = env.list("INTERNAL_IPS", default=[
    "127.0.0.1",
    "localhost",
])

# ─── Jazzmin Admin Theme ──────────────────────────────────────────────────────
from .jazzmin_settings import *

# ─── Frontend URL ─────────────────────────────────────────────────────────────
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
BACKEND_URL = env("BACKEND_URL", default="http://localhost:8000")

# ─── Site Information ─────────────────────────────────────────────────────────
SITE_NAME = "Sotifibre Platform"
SITE_DESCRIPTION = "Plateforme de sécurité pour appareils IoT"
CONTACT_EMAIL = env("CONTACT_EMAIL", default="contact@iotshield.tn")
SUPPORT_EMAIL = env("SUPPORT_EMAIL", default="support@iotshield.tn")


# ─── Grok AI ─────────────────────────────────────────────────────────
GROK_API_KEY = os.environ.get('GROK_API_KEY', '')
GROK_API_ENDPOINT = os.environ.get('GROK_API_ENDPOINT', 'https://api.x.ai/v1/chat/completions')
GROK_MODEL = os.environ.get('GROK_MODEL', 'grok-4.20-reasoning')
GROK_TIMEOUT = int(os.environ.get('GROK_TIMEOUT', 30))
