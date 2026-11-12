"""Réglages uniques du projet, pilotés par des variables d'environnement (décision D10).

En local : copier `.env.example` vers `.env`. En ligne : variables définies chez l'hébergeur.
"""

import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

EN_TEST = "pytest" in sys.modules

DEBUG = env.bool("DEBUG", default=False)
CLE_LOCALE = "cle-locale-non-secrete-a-remplacer" if DEBUG or EN_TEST else ""
SECRET_KEY = env("SECRET_KEY", default=CLE_LOCALE)
if not SECRET_KEY:
    raise RuntimeError("La variable d'environnement SECRET_KEY est obligatoire hors mode DEBUG.")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])
ALLOWED_HOSTS.append(".vercel.app")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://*.vercel.app"])

# Adresse d'administration non standard (ADM-01), à garder pour soi.
ADMIN_URL = env("ADMIN_URL", default="gestion/").strip("/") + "/"

INSTALLED_APPS = [
    "apps.core.site_admin.AdminPortfolioConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "axes",
    "apps.core",
    "apps.portfolio",
    "apps.contact",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.core.middleware.CachePublicMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.contexte.site",
            ],
        },
    },
]

# --- Base de données : SQLite en local, PostgreSQL (Neon, adresse « pooled ») en ligne.
DATABASES = {"default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
if DATABASES["default"]["ENGINE"].endswith("postgresql"):
    # Indispensable avec le pooler de Neon (PgBouncer en mode transaction).
    DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Cache partagé en base : le cache mémoire n'est pas partagé entre instances serverless.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_partage",
    }
}
DUREE_CACHE_PAGES = 60  # secondes, maximum fixé par le cahier des charges

# --- Authentification
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
# Blocage après 5 mots de passe faux pour un identifiant, pendant 1 heure.
# (Par identifiant et non par IP : derrière le proxy de Vercel, l'IP vue n'est pas fiable.
# Déblocage manuel : `python manage.py axes_reset`.)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCKOUT_PARAMETERS = ["username"]
AXES_RESET_ON_SUCCESS = True
# axes.W006 vise les blocages par navigateur ou cookie ; ici le blocage porte sur l'identifiant.
SILENCED_SYSTEM_CHECKS = ["axes.W006"]
AXES_ENABLED = not EN_TEST

# Déconnexion automatique après 30 minutes d'inactivité.
SESSION_COOKIE_AGE = 30 * 60
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --- Langue et fuseau
LANGUAGE_CODE = "fr"
TIME_ZONE = env("TIME_ZONE", default="Africa/Abidjan")
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques (CDN de Vercel en ligne, WhiteNoise en local et en repli)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# --- Médias : Cloudinary si CLOUDINARY_URL est défini, sinon dossier local `media/` (D7)
CLOUDINARY_URL = env("CLOUDINARY_URL", default="")
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {
        "BACKEND": "apps.core.stockage.StockageCloudinary"
        if CLOUDINARY_URL and not EN_TEST
        else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        if DEBUG or EN_TEST
        else "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
TAILLE_MAX_IMAGE = 2 * 1024 * 1024  # 2 Mo
TAILLE_MAX_PDF = 4 * 1024 * 1024  # 4 Mo (Vercel refuse une requête de plus de 4,5 Mo)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --- Emails : notification d'un message de contact.
# Avec Resend : EMAIL_HOST=smtp.resend.com, EMAIL_HOST_USER=resend, EMAIL_HOST_PASSWORD=<clé API>.
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Portfolio <onboarding@resend.dev>")
EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST
    else "django.core.mail.backends.console.EmailBackend"
)

# --- Formulaire de contact : limitation de débit par adresse IP
CONTACT_DEBIT = env("CONTACT_DEBIT", default="5/h")
CONTACT_CONSERVATION_JOURS = 365

# --- Sécurité en ligne
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not EN_TEST)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
