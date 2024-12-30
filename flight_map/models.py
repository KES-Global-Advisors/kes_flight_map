from django.db import models
from django.conf import settings

# Create your models here.
class Program(models.Model):
    """Create a program"""
    name = models.CharField(max_length=255)
    vision = models.TextField()
    time_horizon = models.CharField(max_length=100)
    stakeholders = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="programs")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programs"
        ordering = ["name"]