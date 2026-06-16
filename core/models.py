from django.db import models
from django.conf import settings




# -------------------------
# DEPARTMENTS (ERP STRUCTURE)
# -------------------------
class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# -------------------------
# ERP TRANSACTION CORE
# -------------------------
class Transaction(models.Model):

    TRANSACTION_TYPES = [
        ('waste', 'Waste Intake'),
        ('inventory', 'Inventory Movement'),
        ('finance', 'Financial Transaction'),
        ('hr', 'HR Transaction'),
    ]

    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    description = models.TextField()

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.description}"




class AuditLog(models.Model):

    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('payment', 'Payment'),
        ('purchase_order', 'Purchase Order'),
        ('stock', 'Stock Movement'),
        ('attendance', 'Attendance'),
        ('hr', 'HR Action'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES
    )

    model_name = models.CharField(max_length=100)

    record_id = models.IntegerField(
        null=True,
        blank=True
    )

    description = models.TextField()

    # =========================
    # ERP TRACEABILITY (IMPORTANT)
    # =========================
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    user_agent = models.TextField(
        null=True,
        blank=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user} | {self.action_type} | {self.model_name}"