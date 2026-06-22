from django.http import HttpResponseForbidden
from django.shortcuts import redirect


def role_required(allowed_roles):

    def decorator(view_func):

        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            return HttpResponseForbidden(
                "❌ You are not allowed to access this module"
            )

        return wrapper

    return decorator