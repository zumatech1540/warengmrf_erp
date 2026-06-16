from django.db import models
from core.models import Department
from django.conf import settings



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

    remarks = models.CharField(
        max_length=200,
        blank=True
    )

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
        Employee,
        on_delete=models.CASCADE
    )

    payroll_month = models.CharField(max_length=20)

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

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        self.net_salary = (
            self.basic_salary +
            self.allowances -
            self.deductions
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.payroll_month}"

