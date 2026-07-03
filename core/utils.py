from django.utils import timezone
from .models import AuditLog, Department


def log_action(
    user,
    action_type,
    model_name,
    record_id=None,
    description="",
    ip_address=None,
    user_agent=None
):

    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        model_name=model_name,
        record_id=record_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
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

    return Department.objects.filter(
        name=name
    ).first()