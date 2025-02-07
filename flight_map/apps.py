from django.apps import AppConfig


class FlightMapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flight_map'

    def ready(self):
        import flight_map.signals
