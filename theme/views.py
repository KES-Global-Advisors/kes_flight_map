from django.shortcuts import render
# theme/views.py
from rest_framework import generics
from .models import ThemeConfiguration
from .serializers import ThemeConfigurationSerializer

class ThemeConfigurationRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = ThemeConfigurationSerializer

    def get_object(self):
        # Always get (or create) the one and only configuration record
        obj, created = ThemeConfiguration.objects.get_or_create(pk=1)
        return obj
