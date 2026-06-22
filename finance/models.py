from django.db import models, transaction
from django.conf import settings
from django.utils import timezone  
from decimal import Decimal
from django.db.models import Sum
from core.models import Transaction, Department 

# =========================================================
# INCOME
# =========================================================
class Income(models.Model):
    SOURCE_CHOICES = [
        ('waste_sales', 'Waste Sales'),
        ('recycling', 'Recycling Sales'),
        ('service', 'Service Charges'),
        ('other', 'Other Income'),
    ]

    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    
    department = models.ForeignKey(
        'core.Department', 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        self.amount = Decimal(self.amount or 0)

        with transaction.atomic():
            super().save(*args, **kwargs)

            if not self.transaction:
                self.transaction = Transaction.objects.create(
                    type='income',
                    description=f"{self.source} - {self.amount}",
                    amount=self.amount,
                    created_by=getattr(self, "created_by", None),
                    department=self.department
                )
                super().save(update_fields=['transaction'])

    def __str__(self):
        return f"{self.source} - {self.amount}"



# =========================================================
# EXPENSE
# =========================================================
class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('fuel', 'Fuel'),
        ('salary', 'Salary'),
        ('repairs', 'Repairs'),
        ('utilities', 'Utilities'),
        ('office', 'Office Expenses'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        self.amount = Decimal(self.amount or 0)

        with transaction.atomic():
            super().save(*args, **kwargs)

            if not self.transaction:
                self.transaction = Transaction.objects.create(
                    type='expense',
                    description=f"{self.category} - {self.amount}",
                    amount=self.amount,
                    created_by=getattr(self, "created_by", None)
                )
                super().save(update_fields=['transaction'])

    def __str__(self):
        return f"{self.category} - {self.amount}"


# =========================================================
# ACCOUNT RECEIVABLE (AR)
# =========================================================
class AccountReceivable(models.Model):
    customer_name = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    due_date = models.DateField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def balance(self):
        return self.amount_due - self.amount_paid

    def save(self, *args, **kwargs):
        self.amount_due = Decimal(self.amount_due or 0)
        self.amount_paid = Decimal(self.amount_paid or 0)

        if self.amount_paid >= self.amount_due:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.amount_due}"


# =========================================================
# ACCOUNT PAYABLE (AP)
# =========================================================
class AccountPayable(models.Model):
    supplier_name = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    due_date = models.DateField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('paid', 'Paid'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def balance(self):
        return self.amount_due - self.amount_paid

    def save(self, *args, **kwargs):
        self.amount_due = Decimal(self.amount_due or 0)
        self.amount_paid = Decimal(self.amount_paid or 0)

        if self.amount_paid >= self.amount_due:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_name} - {self.amount_due}"


# =========================================================
# PAYMENT (CRITICAL FIXED LOGIC)
# =========================================================



class Payment(models.Model):

    PAYMENT_TYPE = [
        ('ar', 'Accounts Receivable'),
        ('ap', 'Accounts Payable'),
    ]

    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE)

    ar = models.ForeignKey(
        'AccountReceivable',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    ap = models.ForeignKey(
        'AccountPayable',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50, default='cash')
    reference = models.CharField(max_length=100, blank=True)

    date = models.DateTimeField(default=timezone.now)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    # =========================
    # VALIDATION
    # =========================
    def clean(self):

        if self.payment_type == 'ar' and not self.ar:
            raise ValueError("AR payment requires AccountReceivable")

        if self.payment_type == 'ap' and not self.ap:
            raise ValueError("AP payment requires AccountPayable")

        if self.ar and self.ap:
            raise ValueError("Payment cannot be both AR and AP")

        if Decimal(str(self.amount or 0)) <= 0:
            raise ValueError("Payment amount must be greater than zero")

    # =========================
    # SAVE LOGIC (ERP SAFE)
    # =========================
    def save(self, *args, **kwargs):

        self.amount = Decimal(str(self.amount or 0))

        with transaction.atomic():

            is_new = self.pk is None

            # validate BEFORE saving
            self.full_clean()

            super().save(*args, **kwargs)

            if not is_new:
                return
            from finance.services import create_journal
            # =========================
            # AR PAYMENT
            # =========================
            if self.ar:

                self.ar.amount_paid = Decimal(str(self.ar.amount_paid or 0)) + self.amount
                self.ar.save()

                create_journal(
                    reference=f"PAY-AR-{self.id}",
                    description=f"Customer payment: {self.ar.customer_name}",
                    debit_account="Cash/Bank",
                    credit_account="Accounts Receivable",
                    amount=self.amount,
                    user=self.created_by
                )

            # =========================
            # AP PAYMENT
            # =========================
            elif self.ap:

                self.ap.amount_paid = Decimal(str(self.ap.amount_paid or 0)) + self.amount
                self.ap.save()

                create_journal(
                    reference=f"PAY-AP-{self.id}",
                    description=f"Supplier payment: {self.ap.supplier_name}",
                    debit_account="Accounts Payable",
                    credit_account="Cash/Bank",
                    amount=self.amount,
                    user=self.created_by
                )

    def __str__(self):
        return f"{self.payment_type.upper()} - {self.amount}"

# =========================================================
# GENERAL LEDGER
# =========================================================
class GeneralLedger(models.Model):

    ENTRY_TYPE = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    journal = models.ForeignKey(
        'JournalEntry',
        on_delete=models.CASCADE,
        related_name='ledger_entries',
        null=True,
        blank=True
    )

    account_name = models.CharField(max_length=200)

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(blank=True)

    date = models.DateTimeField(
        auto_now_add=True
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return (
            f"{self.account_name} | "
            f"{self.entry_type.upper()} | "
            f"KES {self.amount}"
        )

# =========================================================
# INVOICE SEQUENCE (THREAD SAFE FIX)
# =========================================================
class InvoiceSequence(models.Model):
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    @staticmethod
    def next_number():
        with transaction.atomic():
            seq, _ = InvoiceSequence.objects.select_for_update().get_or_create(
                year=timezone.now().year
            )
            seq.last_number += 1
            seq.save()
            return seq.last_number

    def __str__(self):
        return f"{self.year} - {self.last_number}"

class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    account = models.CharField(max_length=200)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    description = models.TextField()
    reference_type = models.CharField(max_length=50)  # waste, payment, sale
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)




class JournalEntry(models.Model):

    reference = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField()

    date = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        ordering = ['-date']

    # =========================
    # ERP-GRADE TOTALS
    # =========================
    def total_debits(self):
        return self.lines.filter(entry_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or 0

    def total_credits(self):
        return self.lines.filter(entry_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or 0

    def is_balanced(self):
        return self.total_debits() == self.total_credits()

    def balance_difference(self):
        return self.total_debits() - self.total_credits()

    def __str__(self):
        return self.reference

class JournalLine(models.Model):

    ENTRY_TYPE = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    journal = models.ForeignKey(
        'JournalEntry',
        related_name='lines',
        on_delete=models.CASCADE
    )

    
    account = models.ForeignKey(
        'ChartOfAccount',
        on_delete=models.PROTECT,
        related_name='journal_lines'
    )

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.journal.reference} | {self.account.name} | {self.entry_type} | {self.amount}"

class ChartOfAccount(models.Model):

    ACCOUNT_TYPE = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    code = models.CharField(max_length=20, unique=True)  # e.g. 1000
    name = models.CharField(max_length=200)               # Cash, Bank, AR
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE)

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"



