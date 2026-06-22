from django.db import models
from django.conf import settings




# -------------------------
# DEPARTMENTS (ERP STRUCTURE)
# -------------------------
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True) 

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



from django.db import models
from decimal import Decimal



class Supplier(models.Model):

    # -------------------------
    # BASIC INFO
    # -------------------------
    company_name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)

    phone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Credit'),
    ]

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='mpesa'
    )

    # -------------------------
    # FINANCIAL TRACKING
    # -------------------------
    total_supplied_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    last_payment_date = models.DateTimeField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
     return f"{self.company_name} - {self.phone}"

    # -------------------------
    # BUSINESS LOGIC
    # -------------------------
    def add_supply_value(self, amount):
        amount = Decimal(str(amount))

        self.total_supplied_value += amount
        self.outstanding_balance += amount
        self.save()

    def record_payment(self, amount):
        amount = Decimal(str(amount))

        self.total_paid += amount
        self.outstanding_balance -= amount

        if self.outstanding_balance < 0:
            self.outstanding_balance = Decimal("0.00")

        self.save()