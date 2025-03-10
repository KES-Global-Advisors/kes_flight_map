from .base import *
environ.Env.read_env(os.path.join(BASE_DIR, '.env.prod'))

# Production-specific configurations
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["your-production-domain.com"])

# Database settings (PostgreSQL for production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("POSTGRES_DB"),
        'USER': env("POSTGRES_USER"),
        'PASSWORD': env("POSTGRES_PASSWORD"),
        'HOST': env("POSTGRES_HOST", default="localhost"),
        'PORT': env.int("POSTGRES_PORT", default=5432),
    }
}

# Email settings for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('MAILGUN_SMTP_SERVER', default='smtp.mailgun.org')
EMAIL_PORT = env.int('MAILGUN_SMTP_PORT', default=587)
EMAIL_HOST_USER = env('MAILGUN_SMTP_LOGIN')
EMAIL_HOST_PASSWORD = env('MAILGUN_SMTP_PASSWORD')
EMAIL_USE_TLS = True

# Enhanced security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Content Security Policy Middleware (add to MIDDLEWARE)
MIDDLEWARE += ['csp.middleware.CSPMiddleware']

CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "cdn.example.com"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'", "fonts.googleapis.com"]
CSP_FONT_SRC = ["'self'", "fonts.gstatic.com"]
CSP_IMG_SRC = ["'self'", "data:", "cdn.example.com"]

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Celery configuration
CELERY_TIMEZONE = "UTC"
CELERY_TASK_SERIALIZER = "json"
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'

# Static and media file hosting
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / "logs/errors.log",
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

# production.py
if DEBUG:
    raise ValueError("DEBUG must be False in production!")

if 'localhost' in ALLOWED_HOSTS:
    raise ValueError("Remove localhost from production hosts!")