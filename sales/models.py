from django.db import models
from django.conf import settings
from inventory.models import Item, StockMovement
from core.models import Transaction, Department


class Customer(models.Model):

    company_name = models.CharField(max_length=200)

    contact_person = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    phone = models.CharField(max_length=50)

    email = models.EmailField(
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.company_name


class Sale(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        self.total_amount = (
            self.quantity * self.unit_price
        )

        if is_new:

            if self.item.current_stock < self.quantity:
                raise ValueError(
                    f"Insufficient stock. Available stock is "
                    f"{self.item.current_stock}"
                )

        super().save(*args, **kwargs)

        if is_new:

            # Reduce inventory stock
            self.item.current_stock -= self.quantity
            self.item.save()

            # Create stock movement
            StockMovement.objects.create(
                item=self.item,
                movement_type='out',
                quantity=self.quantity,
                reason=f"Sale #{self.id}",
                created_by=self.created_by
            )

            # Create finance transaction
            finance_department = Department.objects.filter(
                name__icontains='Finance'
            ).first()

            if finance_department:

                Transaction.objects.create(
                    type='finance',
                    department=finance_department,
                    description=f"Sale #{self.id}",
                    amount=self.total_amount,
                    created_by=self.created_by
                )

    def __str__(self):
        return f"Sale #{self.id}"