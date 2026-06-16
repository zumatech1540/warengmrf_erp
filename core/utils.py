from .models import AuditLog
from core.models import Department

from django.utils import timezone

def log_action(user, action_type, model_name, record_id, description=""):

    from core.models import AuditLog

    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        record_id=record_id,
        description=description,
        timestamp=timezone.now()
    )





DEPARTMENT_MAP = {
    "waste": "Waste",
    "inventory": "Inventory",
    "finance": "Finance",
    "hr": "HR",
}

def get_department(transaction_type):
    name = DEPARTMENT_MAP.get(transaction_type)

    if not name:
        return None

    return Department.objects.filter(name=name).first()