# theme/serializers.py
from rest_framework import serializers
from .models import ThemeConfiguration

class ThemeConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThemeConfiguration
        fields = ['theme_color']
