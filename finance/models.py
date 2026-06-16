from django.db import models
from core.models import Transaction
from django.db import models
from django.utils import timezone
from decimal import Decimal

# -------------------------
# INCOME
# -------------------------
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
    date = models.DateField(auto_now_add=True)

    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.source} - {self.amount}"


# -------------------------
# EXPENSE
# -------------------------
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
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.category} - {self.amount}"




# =========================
# ACCOUNTS RECEIVABLE (AR)
# =========================
class AccountReceivable(models.Model):

    customer_name = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    due_date = models.DateField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # -------------------------
    # ERP CORE LOGIC
    # -------------------------
    def get_balance(self):
        return self.amount_due - self.amount_paid

    def update_status(self):
        balance = self.get_balance()

        if balance <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.amount_due}"


# =========================
# ACCOUNTS PAYABLE (AP)
# =========================
class AccountPayable(models.Model):

    supplier_name = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    due_date = models.DateField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # -------------------------
    # ERP CORE LOGIC
    # -------------------------
    def get_balance(self):
        return self.amount_due - self.amount_paid

    def update_status(self):
        balance = self.get_balance()

        if balance <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'

    def save(self, *args, **kwargs):
        self.update_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier_name} - {self.amount_due}"


# =========================
# BANK TRANSACTIONS
# =========================
class BankTransaction(models.Model):
    BANK_TYPE = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    ]

    bank_name = models.CharField(max_length=200)
    transaction_type = models.CharField(max_length=20, choices=BANK_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)
    date = models.DateField(auto_now_add=True)

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.bank_name} - {self.amount}"


# =========================
# GENERAL LEDGER (GL)
# =========================
class GeneralLedger(models.Model):

    ENTRY_TYPE = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    account_name = models.CharField(max_length=200)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField(auto_now_add=True)

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.account_name} - {self.entry_type}"

class Payment(models.Model):

    PAYMENT_TYPE = [
        ('ar', 'Accounts Receivable'),
        ('ap', 'Accounts Payable'),
    ]

    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE)

    ar = models.ForeignKey('AccountReceivable', on_delete=models.CASCADE, null=True, blank=True)
    ap = models.ForeignKey('AccountPayable', on_delete=models.CASCADE, null=True, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=50, default='cash')  # cash, bank, mpesa
    reference = models.CharField(max_length=100, blank=True)

    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.payment_type} - {self.amount}"


class Invoice(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    sales_order = models.OneToOneField(
        'inventory.SalesOrder',
        on_delete=models.CASCADE,
        related_name='invoice'
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True
    )

    customer = models.ForeignKey(
        'inventory.Customer',
        on_delete=models.CASCADE
    )

    invoice_date = models.DateTimeField(auto_now_add=True)

    due_date = models.DateField(null=True, blank=True)

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='issued'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------
    # AUTO CALCULATION
    # -------------------------
    def calculate_totals(self):

        self.subtotal = self.sales_order.total_amount

        self.tax = self.subtotal * 0  # change later if VAT needed

        self.total_amount = self.subtotal + self.tax

        self.balance = self.total_amount - self.amount_paid

    # -------------------------
    # SAVE LOGIC
    # -------------------------
    def save(self, *args, **kwargs):

        self.calculate_totals()

        # update status automatically
        if self.balance <= 0:
            self.status = 'paid'
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        else:
            self.status = 'issued'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number

class InvoiceSequence(models.Model):
    year = models.IntegerField(unique=True)
    last_number = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.year} - {self.last_number}"
