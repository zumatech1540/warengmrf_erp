from django.db import models
from core.models import Department
from django.conf import settings
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal



class Employee(models.Model):

    EMPLOYMENT_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    employee_number = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30)

    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    position = models.CharField(max_length=100)
    hire_date = models.DateField()

    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='active')

    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee_number} - {self.first_name} {self.last_name}"

class Attendance(models.Model):

    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('offday', 'Off Day'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField()

    clock_in = models.TimeField(
        null=True,
        blank=True
    )

    clock_out = models.TimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present'
    )

    working_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    remarks = models.CharField(
        max_length=200,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        from datetime import datetime

        if self.clock_in and self.clock_out:

            start = datetime.combine(
                self.date,
                self.clock_in
            )

            end = datetime.combine(
                self.date,
                self.clock_out
            )

            hours = (
                end - start
            ).total_seconds() / 3600

            self.working_hours = round(max(hours, 0), 2)

            # Company standard = 8 hours
            if self.working_hours > 8:
                self.overtime_hours = round(
                    self.working_hours - 8,
                    2
                )
            else:
                self.overtime_hours = 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.date}"

class LeaveRequest(models.Model):

    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    leave_type = models.CharField(max_length=50)

    start_date = models.DateField()
    end_date = models.DateField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='pending'
    )

    applied_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee} - {self.leave_type}"



class Payroll(models.Model):

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE
    )

    payroll_month = models.CharField(
        max_length=20
    )

    basic_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    allowances = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    deductions = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_paid = models.BooleanField(default=False)

    paid_date = models.DateField(
        null=True,
        blank=True
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-generated_at']

        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'payroll_month'],
                name='unique_employee_payroll_month'
            )
        ]

    def clean(self):

        current_month = timezone.now().strftime("%B %Y")

        # Prevent future payroll
        if self.payroll_month > current_month:
            raise ValidationError(
                "Future payroll months are not allowed."
            )

        # Prevent duplicate payroll
        existing = Payroll.objects.filter(
            employee=self.employee,
            payroll_month=self.payroll_month
        )

        if self.pk:
            existing = existing.exclude(pk=self.pk)

        if existing.exists():
            raise ValidationError(
                f"Payroll already exists for "
                f"{self.employee} ({self.payroll_month})"
            )

    def save(self, *args, **kwargs):

        self.full_clean()

        basic = Decimal(str(self.basic_salary or 0))
        allow = Decimal(str(self.allowances or 0))
        deduct = Decimal(str(self.deductions or 0))

        self.net_salary = basic + allow - deduct

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.payroll_month}"

class SalaryAdvance(models.Model):

    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='pending'
    )

    requested_on = models.DateTimeField(
        auto_now_add=True
    )

    approved_on = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.employee} - {self.amount}"

class LeaveBalance(models.Model):

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE
    )

    annual_leave_days = models.IntegerField(default=21)

    used_leave_days = models.IntegerField(default=0)

    @property
    def remaining_leave_days(self):
        return self.annual_leave_days - self.used_leave_days

    def __str__(self):
        return str(self.employee)

class Payslip(models.Model):

    payroll = models.OneToOneField(
        Payroll,
        on_delete=models.CASCADE
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Payslip - {self.payroll}"

class EmployeeDocument(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    document = models.FileField(
        upload_to='employee_documents/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title

class AssetAssignment(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    asset_name = models.CharField(max_length=200)

    serial_number = models.CharField(
        max_length=100,
        blank=True
    )

    assigned_on = models.DateField()

    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.asset_name} - {self.employee}"