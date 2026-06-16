from django.shortcuts import render
from .models import AuditLog
from django.contrib.auth.decorators import login_required


@login_required
def audit_logs(request):

    logs = AuditLog.objects.all().order_by('-timestamp')

    return render(request, 'core/audit_logs.html', {
        'logs': logs
    })