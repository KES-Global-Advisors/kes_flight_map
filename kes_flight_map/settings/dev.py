from .base import *

# Development-specific configurations
DEBUG = False

ALLOWED_HOSTS = [
    "api.kesglobaladvisors.com",
    "134.209.75.92",
    "localhost",
    "127.0.0.1"
]


# Local database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kes_flight_map',  # Your local database name
        'USER': 'kes_flightmap',   # Your local database username
        'PASSWORD': 'kes@2024',    # Your local database password
        'HOST': 'localhost',       # Database host
        'PORT': '5432',            # Database port
    }
}

# Email backend for development
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Update dev.py email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Use SMTP even in dev
EMAIL_HOST = env('DEV_EMAIL_HOST', default='smtp.mailtrap.io')
EMAIL_HOST_USER = env('DEV_EMAIL_USER', default='')
EMAIL_HOST_PASSWORD = env('DEV_EMAIL_PASSWORD', default='')
EMAIL_PORT = env.int('DEV_EMAIL_PORT', default=2525)
