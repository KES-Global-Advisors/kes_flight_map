from .base import *

# Development-specific configurations
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

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
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
