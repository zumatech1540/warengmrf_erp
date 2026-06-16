from django.db import models
from django.conf import settings
from core.models import Transaction, Department


# -------------------------
# WASTE CATEGORY
# -------------------------
class WasteCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# -------------------------
# WASTE INTAKE (ERP CORE ENTRY)
# -------------------------
class WasteIntake(models.Model):

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    category = models.ForeignKey(WasteCategory, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    source = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.quantity}"

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        super().save(*args, **kwargs)

        # ERP CORE INTEGRATION
        if is_new:

            Transaction.objects.create(
                type='waste',
                department=self.department,
                description=f"Waste intake: {self.category.name} | Qty: {self.quantity} | Source: {self.source}",
                amount=0,
                created_by=self.created_by
            )




class WasteStatusHistory(models.Model):

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    waste = models.ForeignKey('WasteIntake', on_delete=models.CASCADE)

    old_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    comment = models.TextField(blank=True, null=True)

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.waste.id} {self.old_status} → {self.new_status}"