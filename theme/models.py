# theme/models.py
from django.db import models

class ThemeConfiguration(models.Model):
    theme_color = models.CharField(
        max_length=7,
        default="#3B82F6",  # default blue; include the '#' in the value
        help_text="Primary theme color (hex format)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Theme: {self.theme_color}"
