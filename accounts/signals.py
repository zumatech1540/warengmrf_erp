from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out
)

from django.dispatch import receiver
from django.utils import timezone

from .models import LoginActivity


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):

    LoginActivity.objects.create(
        user=user,
        ip_address=request.META.get(
            "REMOTE_ADDR"
        ),
        user_agent=request.META.get(
            "HTTP_USER_AGENT",
            ""
        )
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):

    if not user:
        return

    activity = LoginActivity.objects.filter(
        user=user,
        logout_time__isnull=True
    ).last()

    if activity:

        activity.logout_time = timezone.now()

        activity.save()