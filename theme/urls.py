# theme/urls.py
from django.urls import path
from .views import ThemeConfigurationRetrieveUpdateView

urlpatterns = [
    path('theme/', ThemeConfigurationRetrieveUpdateView.as_view(), name='theme-config'),
]
