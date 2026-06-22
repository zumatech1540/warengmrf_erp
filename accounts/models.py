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