from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
    ('super_admin', 'Super Admin'),

    ('manager', 'Manager'),

    ('collection', 'Waste Collector'),

    ('hr', 'HR'),

    ('finance', 'Finance'),
    ('waste', 'Waste Management'),

    ('inventory', 'Inventory'),
]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='viewer'
    )

    phone = models.CharField(max_length=20, blank=True)

    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

# accounts/models.py

from django.db import models
from django.conf import settings


class LoginActivity(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    ip_address = models.CharField(
        max_length=100,
        blank=True
    )

    user_agent = models.TextField(
        blank=True
    )

    login_time = models.DateTimeField(
        auto_now_add=True
    )

    logout_time = models.DateTimeField(
        null=True,
        blank=True
    )

    successful = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"