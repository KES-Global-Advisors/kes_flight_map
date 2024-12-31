from .production import *

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
