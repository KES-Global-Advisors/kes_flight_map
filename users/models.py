from django.contrib.auth.models import AbstractUser, Group, Permission, UserManager
from django.db import models, transaction

class CustomUserManager(UserManager):
    @transaction.atomic
    def create_user(self, username, email=None, password=None, **extra_fields):
        # If no admin exists yet, make this first user an admin
        if not self.filter(role='admin').exists():
            extra_fields.setdefault('role', 'admin')
        else:
            extra_fields.setdefault('role', 'viewer')
        return super().create_user(username, email, password, **extra_fields)

    @transaction.atomic
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_set",
        blank=True,
    )

    objects = CustomUserManager()

    def __str__(self):
        return self.username
