from .production import *
environ.Env.read_env(os.path.join(BASE_DIR, '.env.private'))

# Private cloud-specific configurations
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["private-cloud.example.com"])

# Database settings (PostgreSQL for private cloud)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("PRIVATE_POSTGRES_DB"),
        'USER': env("PRIVATE_POSTGRES_USER"),
        'PASSWORD': env("PRIVATE_POSTGRES_PASSWORD"),
        'HOST': env("PRIVATE_POSTGRES_HOST", default="private-db.example.com"),
        'PORT': env.int("PRIVATE_POSTGRES_PORT", default=5432),
    }
}

# Static and media file hosting for private cloud
STATIC_URL = 'https://static.private-cloud.example.com/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = 'https://static.private-cloud.example.com/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Security settings (additional private cloud-specific measures)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Add to private_cloud.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('PRIVATE_SMTP_HOST')
EMAIL_PORT = env.int('PRIVATE_SMTP_PORT', default=587)
EMAIL_HOST_USER = env('PRIVATE_SMTP_USER')
EMAIL_HOST_PASSWORD = env('PRIVATE_SMTP_PASSWORD')
EMAIL_USE_TLS = True

# Private cloud specific security
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']  # Allow health checks over HTTP
SECURE_REFERRER_POLICY = 'same-origin'