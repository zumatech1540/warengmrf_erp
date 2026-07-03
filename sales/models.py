from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils import timezone
from inventory.models import Item, StockMovement
from core.models import Transaction, Department
from django.conf import settings
from django.db import models
from django.utils import timezone

from inventory.models import Item, StockMovement
from core.models import Transaction, Department

from decimal import Decimal


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

    created_at = models.DateTimeField(
        auto_now_add=True
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

    # Normal waste sales (KG)
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Timber fields
    timber_size = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    timber_length = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    timber_pieces = models.PositiveIntegerField(
        default=0
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
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
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # ==========================
        # SAFE DECIMAL CONVERSION
        # ==========================
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))

        # Timber uses pieces
        if self.timber_pieces and self.timber_pieces > 0:
            qty = Decimal(str(self.timber_pieces))

        self.total_amount = qty * price

        # ==========================
        # STOCK VALIDATION
        # ==========================
        if is_new:

            available_stock = Decimal(
                str(self.item.current_stock or 0)
            )

            if available_stock < qty:

                raise ValueError(
                    f"Insufficient stock. "
                    f"Available: {available_stock}"
                )

        super().save(*args, **kwargs)

        if not is_new:
            return

        # ==========================
        # REDUCE STOCK
        # ==========================
        self.item.current_stock = (
            Decimal(str(self.item.current_stock))
            - qty
        )

        self.item.save()

        # ==========================
        # STOCK MOVEMENT
        # ==========================
        movement_reason = f"Sale #{self.id}"

        if self.timber_size:
            movement_reason += (
                f" | {self.timber_size}"
            )

        if self.timber_length:
            movement_reason += (
                f" | {self.timber_length}"
            )

        StockMovement.objects.create(
            item=self.item,
            movement_type='out',
            quantity=qty,
            reason=movement_reason,
            created_by=self.created_by
        )

        # ==========================
        # FINANCE TRANSACTION
        # ==========================
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

        # ==========================
        # ACCOUNTS RECEIVABLE
        # ==========================
        if self.status == 'pending':

            try:

                from finance.models import AccountReceivable

                AccountReceivable.objects.create(
                    customer_name=self.customer.company_name,
                    amount_due=self.total_amount,
                    amount_paid=0,
                    description=f"Sale #{self.id}",
                    due_date=timezone.now().date()
                )

            except Exception as e:

                print(
                    f"Accounts Receivable Error: {e}"
                )

    def __str__(self):

        return (
            f"Sale #{self.id} - "
            f"{self.customer.company_name}"
        )
        




class Sale(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE
    )

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE
    )

    # ==========================
    # NORMAL WASTE SALES (KG)
    # ==========================
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================
    # TIMBER SALES
    # ==========================
    timber_size = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    timber_length = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    timber_pieces = models.PositiveIntegerField(
        default=0
    )

    # ==========================
    # PRICING
    # ==========================
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================
    # PAYMENT STATUS
    # ==========================
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # =====================================
        # DETERMINE SALE QUANTITY
        # =====================================
        if self.timber_pieces and self.timber_pieces > 0:

            sale_qty = Decimal(
                str(self.timber_pieces)
            )

        else:

            sale_qty = Decimal(
                str(self.quantity or 0)
            )

        price = Decimal(
            str(self.unit_price or 0)
        )

        self.total_amount = sale_qty * price

        # =====================================
        # STOCK VALIDATION
        # =====================================
        if is_new:

            available_stock = Decimal(
                str(self.item.current_stock or 0)
            )

            if available_stock < sale_qty:

                raise ValueError(
                    f"Insufficient stock. "
                    f"Available stock is {available_stock}"
                )

        super().save(*args, **kwargs)

        if not is_new:
            return

        # =====================================
        # REDUCE INVENTORY
        # =====================================
        self.item.current_stock = (
            Decimal(str(self.item.current_stock))
            - sale_qty
        )

        self.item.save()

        # =====================================
        # STOCK MOVEMENT
        # =====================================
        reason = f"Sale #{self.id}"

        if self.timber_size:
            reason += f" | Size: {self.timber_size}"

        if self.timber_length:
            reason += f" | Length: {self.timber_length}"

        StockMovement.objects.create(
            item=self.item,
            movement_type="out",
            quantity=sale_qty,
            reason=reason,
            created_by=self.created_by
        )

        # =====================================
        # FINANCE TRANSACTION
        # =====================================
        finance_department = Department.objects.filter(
            name__icontains="Finance"
        ).first()

        if finance_department:

            Transaction.objects.create(
                type="finance",
                department=finance_department,
                description=f"Sale #{self.id}",
                amount=self.total_amount,
                created_by=self.created_by
            )

        # =====================================
        # ACCOUNTS RECEIVABLE
        # =====================================
        if self.status == "pending":

            try:

                from finance.models import AccountReceivable

                AccountReceivable.objects.create(
                    customer_name=self.customer.company_name,
                    amount_due=self.total_amount,
                    amount_paid=0,
                    description=f"Sale #{self.id}",
                    due_date=timezone.now().date()
                )

            except Exception as e:

                print(
                    f"Accounts Receivable Error: {e}"
                )

        # =====================================
        # AUTO CREATE INVOICE
        # =====================================
        try:

            Invoice.objects.create(
                sale=self,
                invoice_number=f"INV-{self.id:05d}",
                customer_name=self.customer.company_name,
                total_amount=self.total_amount,
                status=self.status
            )

        except Exception as e:

            print(
                f"Invoice Creation Error: {e}"
            )

    def __str__(self):

        return (
            f"Sale #{self.id} - "
            f"{self.customer.company_name}"
        )