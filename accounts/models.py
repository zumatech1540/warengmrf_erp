from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('director', 'Managing Director'),
        ('operations', 'Operations Manager'),
        ('finance', 'Finance Manager'),
        ('hr', 'HR Manager'),
        ('inventory', 'Inventory Officer'),
        ('collection', 'Collection Officer'),
        ('data_entry', 'Data Entry Clerk'),
        ('viewer', 'Viewer'),
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