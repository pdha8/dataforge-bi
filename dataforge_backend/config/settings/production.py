"""
Production settings for Render deployment.

Variables d'environnement requises sur Render :
- SECRET_KEY                (auto-generate via render.yaml)
- DATABASE_URL              (auto-injecté par le service Postgres de Render)
- ALLOWED_HOSTS             (ex: ".onrender.com,mondomaine.com")
- CORS_ALLOWED_ORIGINS      (ex: "https://mon-front.onrender.com")
- CSRF_TRUSTED_ORIGINS      (ex: "https://mon-front.onrender.com")
- DJANGO_SETTINGS_MODULE    = "config.settings.production"

Optionnelles :
- DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD / DJANGO_SUPERUSER_USERNAME
- REDIS_URL, SENDGRID_API_KEY, TWILIO_*, etc.
"""
import os
from pathlib import Path

import dj_database_url

from .base import *  # noqa

# ─── Sécurité ────────────────────────────────────────────────────────────────
DEBUG = False

SECRET_KEY = env("SECRET_KEY")

# ALLOWED_HOSTS : injecter via env. Render fournit RENDER_EXTERNAL_HOSTNAME.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)
# Accepter aussi les wildcards type ".onrender.com"
if ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")

# ─── Base de données : DATABASE_URL injecté par Render ──────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=env("DATABASE_URL", default=""),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ─── CORS / CSRF ─────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[
    "https://dataforge-app.onrender.com",
])
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[
    "https://dataforge-app.onrender.com",
    "https://*.onrender.com",
])

# ─── Static files (WhiteNoise) ──────────────────────────────────────────────
# Le middleware WhiteNoise est déjà inséré dans base.py en 2e position.
# On utilise la variante NON-manifest : plus tolérante si un asset tiers
# (Jazzmin, drf_yasg) référence un fichier manquant — sinon TOUT casse.
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# STATICFILES_DIRS : ne pas planter si `static/` n'existe pas dans le repo.
_static_dir = Path(BASE_DIR) / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.is_dir() else []

# WhiteNoise : autoriser les noms de fichier non-trouvés en mode warning
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_USE_FINDERS = True  # fallback finders si manifest absent

# ─── Sécurité HTTP ───────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
# Exempter les health-checks Render (appels HTTP internes 10.x → pas de redirect HTTPS)
SECURE_REDIRECT_EXEMPT = [r"^api/health/?$", r"^health/?$"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# ─── Channels : Redis si dispo, sinon InMemory ──────────────────────────────
_redis_url = os.environ.get("REDIS_URL")
if _redis_url:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [_redis_url]},
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }

# ─── Email ──────────────────────────────────────────────────────────────────
if os.environ.get("SENDGRID_API_KEY"):
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─── Logging : stdout uniquement ────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
