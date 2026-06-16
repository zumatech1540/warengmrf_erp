from django.db import models, transaction
from django.conf import settings
import uuid


# -------------------------
# ITEM MASTER (PRODUCTS/STOCK)
# -------------------------

class Item(models.Model):

    CATEGORY_CHOICES = [
        ('plastic', 'Plastic'),
        ('metal', 'Metal'),
        ('paper', 'Paper'),
        ('organic', 'Organic'),
        ('glass', 'Glass'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    description = models.TextField(blank=True)

    unit = models.CharField(max_length=50)

    # =========================
    # STOCK CONTROL
    # =========================
    current_stock = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    reorder_level = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=10
    )

    reorder_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=20
    )

    # =========================
    # FINANCE INTEGRATION
    # =========================
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # =========================
    # BUSINESS LOGIC
    # =========================
    def low_stock(self):
        return self.current_stock <= self.reorder_level

    def stock_value(self):
        return self.current_stock * self.unit_price

    def __str__(self):
        return self.name
# -------------------------
# STOCK MOVEMENTS
# -------------------------
class StockMovement(models.Model):

    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - {self.movement_type}"

    def save(self, *args, **kwargs):

        item = self.item

        if self.movement_type == 'in':
            item.current_stock += self.quantity

        elif self.movement_type == 'out':

            if item.current_stock < self.quantity:
                raise ValueError(
                    f"Insufficient stock for {item.name}"
                )

            item.current_stock -= self.quantity

        item.save()

        super().save(*args, **kwargs)




class Supplier(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
    ]

    company_name = models.CharField(max_length=200)

    contact_person = models.CharField(
        max_length=200,
        blank=True
    )

    phone = models.CharField(max_length=50)

    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # =========================
    # ERP FINANCE TRACKING
    # =========================

    total_supplied_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    outstanding_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    last_payment_date = models.DateTimeField(
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

    # =========================
    # BUSINESS HELPERS (IMPORTANT)
    # =========================

    def add_supply_value(self, amount):
        """
        Called when Purchase Order is received
        """
        self.total_supplied_value += amount
        self.outstanding_balance += amount
        self.save()

    def record_payment(self, amount):
        """
        Called when supplier is paid
        """
        self.total_paid += amount
        self.outstanding_balance -= amount

        if self.outstanding_balance < 0:
            self.outstanding_balance = 0

        self.save()
class Customer(models.Model):

    company_name = models.CharField(max_length=200)

    contact_person = models.CharField(
        max_length=200,
        blank=True
    )

    phone = models.CharField(max_length=50)

    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.company_name

from django.db import models
from django.conf import settings


class PurchaseOrder(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True)

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.CASCADE
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_number

    def receive_order(self):

        if self.status == 'received':
            return

        self.status = 'received'
        self.save()

        from .models import StockMovement

        for po_item in self.items.all():

            StockMovement.objects.create(
                item=po_item.item,
                movement_type='in',
                quantity=po_item.quantity,
                reason=f"Purchase Order {self.po_number}",
                created_by=self.created_by
            )




class SalesOrder(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE
    )

    order_number = models.CharField(
        max_length=50,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    order_date = models.DateTimeField(auto_now_add=True)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------
    # TOTAL CALCULATION (SAFE)
    # -------------------------
    def calculate_total(self):

        total = sum(
            item.total for item in self.items.all()
        )

        SalesOrder.objects.filter(pk=self.pk).update(
            total_amount=total
        )

        self.total_amount = total

    # -------------------------
    # CREATE ACCOUNT RECEIVABLE
    # -------------------------
    def create_receivable(self):

        from finance.models import AccountReceivable

        if hasattr(self, 'receivable'):
            return

        AccountReceivable.objects.create(
            customer=self.customer,
            sales_order=self,
            invoice_number=f"INV-{str(self.pk).zfill(6)}",
            total_amount=self.total_amount,
            amount_paid=0,
            balance=self.total_amount
        )

    # -------------------------
    # CREATE INVOICE
    # -------------------------
    def create_invoice(self):

        from finance.models import Invoice

        if hasattr(self, 'invoice'):
            return

        Invoice.objects.create(
            sales_order=self,
            customer=self.customer,
            invoice_number=f"INV-{str(self.pk).zfill(6)}"
        )

    # -------------------------
    # MAIN SAVE LOGIC
    # -------------------------
    def save(self, *args, **kwargs):

        is_new = self.pk is None
        old_status = None

        if not is_new:
            old_status = SalesOrder.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        # always update totals
        self.calculate_total()

        # trigger invoice/AR only when completed
        if old_status != 'completed' and self.status == 'completed':
            self.create_receivable()
            self.create_invoice()

    def __str__(self):
        return self.order_number
        
from django.db import models

class PurchaseOrderItem(models.Model):

    purchase_order = models.ForeignKey(
        'PurchaseOrder',
        on_delete=models.CASCADE,
        related_name="items"
    )

    item = models.ForeignKey(
        'Item',
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

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)



class SalesOrderItem(models.Model):

    sales_order = models.ForeignKey(
        'SalesOrder',
        on_delete=models.CASCADE,
        related_name='items'
    )

    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def save(self, *args, **kwargs):

        from django.db import transaction
        from inventory.models import StockMovement, Item

        self.total = self.quantity * self.unit_price

        with transaction.atomic():

            item = Item.objects.select_for_update().get(pk=self.item.pk)

            # =========================
            # UPDATE EXISTING ITEM
            # =========================
            if self.pk:

                old = SalesOrderItem.objects.get(pk=self.pk)
                difference = self.quantity - old.quantity

                # increase sale (reduce stock)
                if difference > 0:

                    if item.current_stock < difference:
                        raise ValueError(
                            f"Insufficient stock for {item.name}"
                        )

                    item.current_stock -= difference

                    StockMovement.objects.create(
                        item=item,
                        movement_type='out',
                        quantity=difference,
                        reason="Sales Order Update (Increase)",
                        created_by=self.sales_order.created_by
                    )

                # decrease sale (return stock)
                elif difference < 0:

                    item.current_stock += abs(difference)

                    StockMovement.objects.create(
                        item=item,
                        movement_type='in',
                        quantity=abs(difference),
                        reason="Sales Order Update (Decrease)",
                        created_by=self.sales_order.created_by
                    )

            # =========================
            # NEW ITEM
            # =========================
            else:

                if item.current_stock < self.quantity:
                    raise ValueError(
                        f"Insufficient stock for {item.name}"
                    )

                item.current_stock -= self.quantity

                StockMovement.objects.create(
                    item=item,
                    movement_type='out',
                    quantity=self.quantity,
                    reason="Sales Order Created",
                    created_by=self.sales_order.created_by
                )

            item.save()

            super().save(*args, **kwargs)

        # recalculate total after save
        self.sales_order.calculate_total()

class AccountReceivable(models.Model):

    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)

    sales_order = models.OneToOneField(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='receivable'
    )

    invoice_number = models.CharField(max_length=50, unique=True)

    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
        ],
        default='unpaid'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.balance = self.total_amount - self.amount_paid

        if self.balance <= 0:
            self.status = "paid"
        elif self.amount_paid > 0:
            self.status = "partial"
        else:
            self.status = "unpaid"

        super().save(*args, **kwargs)