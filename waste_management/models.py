import os
from decimal import Decimal

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone

# Core module
from core.models import Transaction

# Inventory module
from inventory.models import Item, StockMovement
from core.models import Supplier
class WasteCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

# ==========================================================
# 2. WASTE INTAKE (INTERNAL PROCESSING - NO COST)
# ==========================================================
from decimal import Decimal
from django.db import models
from django.conf import settings

from core.models import Transaction
from inventory.models import Item, StockMovement


class WasteIntake(models.Model):

    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    # =========================
    # CORE FIELDS
    # =========================
    category = models.ForeignKey('WasteCategory', on_delete=models.CASCADE)

    supplier = models.ForeignKey(
        'core.Supplier',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='received'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # =========================
    # MEDIA SUPPORT (PWA READY)
    # =========================
    photo = models.ImageField(
        upload_to='waste_photos/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.quantity} KG"

    def save(self, *args, **kwargs):

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if not is_new:
            return

        supplier_name = (
    f"{self.supplier.company_name} ({self.supplier.phone})"
    if self.supplier else "Walk-in / Unknown"
)
        category_name = self.category.name if self.category else "Unassigned"
        

        try:
            Transaction.objects.create(
                type='waste_intake',
                description=f"INTAKE: {category_name} | {self.quantity} KG from {supplier_name}",
                amount=0,
                created_by=self.created_by
            )
        except Exception as e:
            print("Transaction log error:", e)

        try:
            category_slug = category_name.strip().lower()
            valid_categories = ['plastic', 'metal', 'paper', 'organic', 'glass', 'other']
            item_category = category_slug if category_slug in valid_categories else 'other'

            item, _ = Item.objects.get_or_create(
                name=category_name,
                defaults={
                    "category": item_category,
                    "unit": "kg"
                }
            )

            StockMovement.objects.create(
                item=item,
                movement_type='in',
                quantity=Decimal(str(self.quantity)),
                reason=f"Waste Intake - {supplier_name}",
                created_by=self.created_by
            )

        except Exception as e:
            print("Inventory sync error:", e)

# ==========================================================
# 3. WASTE STATUS HISTORY (WORKFLOW AUDIT TRAIL)
# ==========================================================
class WasteStatusHistory(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
    ]

    waste = models.ForeignKey(WasteIntake, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    new_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Waste Status Histories"

    def __str__(self):
        return f"Waste {self.waste.id}: {self.old_status} → {self.new_status}"

# ==========================================================
# 4. WASTE PURCHASE (COMMERCIAL SUPPLIER PROCUREMENT)
# ==========================================================




import logging

logger = logging.getLogger(__name__)


class WastePurchase(models.Model):

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    category = models.ForeignKey(WasteCategory, on_delete=models.PROTECT)

    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        default=0
    )

    is_paid_on_delivery = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supplier.name} - {self.category.name} ({self.quantity} KG)"

    # ======================================================
    # PROFESSIONAL SAVE LOGIC (ATOMIC + SAFE)
    # ======================================================
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        # SAFE DECIMAL HANDLING
        qty = Decimal(str(self.quantity or 0))
        price = Decimal(str(self.unit_price or 0))
        self.total_amount = qty * price

        # SAVE FIRST (required for FK id access)
        super().save(*args, **kwargs)

        if not is_new:
            return

        supplier_name = getattr(self.supplier, "company_name", "Unknown")
        
        category_name = self.category.name if self.category else "Unassigned"

        try:
            with transaction.atomic():

                # ======================================================
                # 1. INVENTORY SYNC
                # ======================================================
                item, _ = Item.objects.get_or_create(
                    name=category_name,
                    defaults={
                        "category": "other",
                        "unit": "kg",
                        "unit_price": price
                    }
                )

                StockMovement.objects.create(
                    item=item,
                    movement_type="in",
                    quantity=qty,
                    reason=f"Waste Purchase #{self.id} from {supplier_name}",
                    created_by=self.created_by
                )

                # ======================================================
                # 2. FINANCE MODULE
                # ======================================================
                from finance.models import AccountPayable, Payment

                paid_amount = self.total_amount if self.is_paid_on_delivery else Decimal("0")

                ap = AccountPayable.objects.create(
                    supplier_name=supplier_name,
                    amount_due=self.total_amount,
                    amount_paid=paid_amount,
                    description=f"Waste Purchase #{self.id}",
                    due_date=timezone.now().date()
                )

                if self.is_paid_on_delivery:
                    Payment.objects.create(
                        payment_type="ap",
                        ap=ap,
                        amount=self.total_amount,
                        method=self.supplier.payment_method if self.supplier else "cash",
                        reference=f"WP-{self.id}",
                        date=timezone.now()
                    )

                # ======================================================
                # 3. CORE TRANSACTION LOG
                # ======================================================
                Transaction.objects.create(
                    type="waste_purchase",
                    description=f"{category_name} | {qty} KG | KES {self.total_amount}",
                    amount=self.total_amount,
                    created_by=self.created_by
                )

        except Exception as e:
            logger.error(f"WastePurchase sync failed: {e}", exc_info=True)
            # optional: re-raise in production
            # raise