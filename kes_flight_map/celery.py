# kes_flight_map/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kes_flight_map.settings.production')
app = Celery('kes_flight_map')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()