from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

# The class MUST be named 'Command'
class Command(BaseCommand):
    help = 'Creates an admin user with Super Admin role'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@naiberi.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'naiberi@123')

        user, created = User.objects.get_or_create(username=username)
        
        user.email = email
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.role = 'Super Admin' # Only if this field exists in your model
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} permissions updated.'))