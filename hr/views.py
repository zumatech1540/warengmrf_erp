from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from core.models import AuditLog
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from accounts.decorators import role_required
from .models import (
    Employee,
    Attendance,
    LeaveRequest,
    Payroll,
    SalaryAdvance
)
from accounts.models import User

# --- HOME & DASHBOARD ---

@login_required
@role_required(["hr", "super_admin", "director"])
def hr_home(request):
    return render(request, 'hr/hr_home.html')




@login_required
@role_required(["hr", "super_admin", "director"])
def hr_dashboard(request):

    today = timezone.now().date()

    # ==========================================
    # EMPLOYEE STATISTICS
    # ==========================================
    active_employee_qs = Employee.objects.filter(
        status='active'
    )

    total_employees = active_employee_qs.count()

    active_employees = total_employees

    inactive_employees = Employee.objects.filter(
        status='inactive'
    ).count()

    terminated_employees = Employee.objects.filter(
        status='terminated'
    ).count()

    # ==========================================
    # NEW HIRES THIS MONTH
    # ==========================================
    new_hires_month = Employee.objects.filter(
        hire_date__year=today.year,
        hire_date__month=today.month
    ).count()

    # ==========================================
    # EMPLOYEES WITHOUT USER ACCOUNTS
    # ==========================================
    unlinked_employees = Employee.objects.filter(
        user__isnull=True
    ).count()

    # ==========================================
    # LEAVE STATISTICS
    # ==========================================
    pending_leaves = LeaveRequest.objects.filter(
        status='pending'
    ).count()

    approved_leaves = LeaveRequest.objects.filter(
        status='approved'
    ).count()
    
    rejected_leaves = LeaveRequest.objects.filter(
        status='rejected'
    ).count()

    employees_on_leave = LeaveRequest.objects.filter(
        status='approved',
        start_date__lte=today,
        end_date__gte=today
    ).count()

    # ==========================================
    # ATTENDANCE STATISTICS
    # ==========================================
    present_today = Attendance.objects.filter(
        employee__status='active',
        date=today,
        clock_in__isnull=False
    ).count()

    absent_today = max(
        total_employees - present_today,
        0
    )

    late_today = 0  # Future enhancement

    # ==========================================
    # PAYROLL STATISTICS
    # ==========================================
    current_month = today.strftime("%B %Y")

    payroll_qs = Payroll.objects.filter(
        payroll_month=current_month
    )

    payroll_total = payroll_qs.aggregate(
        total=Sum('net_salary')
    )['total'] or 0

    payroll_count = payroll_qs.count()

    payroll_completion = 0

    if total_employees > 0:
        payroll_completion = round(
            (payroll_count / total_employees) * 100,
            2
        )

    # ==========================================
    # SALARY ADVANCE STATISTICS
    # ==========================================
    pending_advances = SalaryAdvance.objects.filter(
        status='pending'
    ).count()

    approved_advances = SalaryAdvance.objects.filter(
        status='approved'
    ).count()

    rejected_advances = SalaryAdvance.objects.filter(
        status='rejected'
    ).count()

    advance_amount = SalaryAdvance.objects.filter(
        status='approved'
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # ==========================================
    # RECENT EMPLOYEES
    # ==========================================
    recent_employees = Employee.objects.select_related(
        'department'
    ).order_by(
        '-created_at'
    )[:10]

    # ==========================================
    # RECENT LEAVE REQUESTS
    # ==========================================
    recent_leaves = LeaveRequest.objects.select_related(
        'employee'
    ).order_by(
        '-applied_on'
    )[:10]

    # ==========================================
    # RECENT PAYROLLS
    # ==========================================
    recent_payrolls = Payroll.objects.select_related(
        'employee'
    ).order_by(
        '-generated_at'
    )[:10]

    # ==========================================
    # DEPARTMENT SUMMARY
    # ==========================================
    department_summary = Employee.objects.values(
        'department__name'
    ).annotate(
        total=Count('id')
    ).order_by(
        '-total'
    )

    # ==========================================
    # DASHBOARD CONTEXT
    # ==========================================
    context = {

        # Employee Stats
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'terminated_employees': terminated_employees,
        'new_hires_month': new_hires_month,
        'unlinked_employees': unlinked_employees,

        # Attendance
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,

        # Leave
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'employees_on_leave': employees_on_leave,

        # Payroll
        'payroll_total': payroll_total,
        'payroll_count': payroll_count,
        'payroll_completion': payroll_completion,
        'current_month': current_month,

        # Salary Advances
        'pending_advances': pending_advances,
        'approved_advances': approved_advances,
        'rejected_advances': rejected_advances,
        'advance_amount': advance_amount,

        # Lists
        'recent_employees': recent_employees,
        'recent_leaves': recent_leaves,
        'recent_payrolls': recent_payrolls,
        'department_summary': department_summary,

        # System
        'today': today,
    }

    return render(
        request,
        'hr/dashboard.html',
        context
    )
# --- EMPLOYEE MANAGEMENT ---

@login_required
@role_required(["hr", "super_admin", "director"])
def employee_list(request):
    employees = Employee.objects.all().order_by('-created_at')
    return render(request, 'hr/employee_list.html', {'employees': employees})

from django.contrib.auth import get_user_model
from core.models import Department
from decimal import Decimal

User = get_user_model()


@login_required
@role_required(["hr", "super_admin", "director"])
def add_employee(request):

    from django.contrib.auth import get_user_model
    from core.models import Department

    User = get_user_model()

    if request.method == "POST":

        employee_number = request.POST['employee_number']

        if Employee.objects.filter(
            employee_number=employee_number
        ).exists():

            return render(
                request,
                'hr/add_employee.html',
                {
                    'users': User.objects.all(),
                    'departments': Department.objects.all(),
                    'error': 'Employee number already exists.'
                }
            )

        user_id = request.POST.get('user')

        linked_user = None

        if user_id:
            linked_user = User.objects.filter(
                id=user_id
            ).first()

            if Employee.objects.filter(
                user=linked_user
            ).exists():

                return render(
                    request,
                    'hr/add_employee.html',
                    {
                        'users': User.objects.all(),
                        'departments': Department.objects.all(),
                        'error': 'User already linked to another employee.'
                    }
                )

        Employee.objects.create(
            user=linked_user,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            employee_number=employee_number,
            email=request.POST.get('email', ''),
            phone=request.POST['phone'],
            position=request.POST['position'],
            department_id=request.POST['department'],
            hire_date=request.POST['hire_date'],
            basic_salary=Decimal(
                request.POST.get('basic_salary', 0)
            ),
            address=request.POST.get('address', ''),
            emergency_contact_name=request.POST.get(
                'emergency_contact_name', ''
            ),
            emergency_contact_phone=request.POST.get(
                'emergency_contact_phone', ''
            )
        )

        return redirect('employee_list')

    return render(
        request,
        'hr/add_employee.html',
        {
            'users': User.objects.all(),
            'departments': Department.objects.all(),
        }
    )
@login_required
@role_required(["hr", "super_admin", "director"])
def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == "POST":
        employee.first_name = request.POST['first_name']
        employee.last_name = request.POST['last_name']
        employee.phone = request.POST['phone']
        employee.position = request.POST['position']
        employee.basic_salary = Decimal(request.POST.get('basic_salary', 0))
        employee.status = request.POST['status']
        employee.save()
        return redirect('employee_list')

    return render(request, 'hr/edit_employee.html', {'employee': employee})

@login_required
@role_required(["hr", "super_admin", "director"])
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    return render(request, 'hr/employee_detail.html', {'employee': employee})

# --- ATTENDANCE MANAGEMENT ---

@login_required
@role_required(["hr", "super_admin", "director"])
def mark_attendance(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    today = date.today()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today
    )

    if request.method == "POST":
        if not attendance.clock_in:
            attendance.clock_in = request.POST.get('clock_in')
        else:
            attendance.clock_out = request.POST.get('clock_out')
        attendance.save()
        return redirect('employee_detail', employee_id=employee.id)

    return render(request, 'hr/mark_attendance.html', {
        'employee': employee,
        'attendance': attendance
    })

@login_required
@role_required(["hr", "super_admin", "director"])
def attendance_list(request):
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        return render(request, 'hr/no_employee.html')

    attendance = Attendance.objects.filter(employee=employee).order_by('-date')
    today_attendance = Attendance.objects.filter(employee=employee, date=date.today()).first()

    return render(request, 'hr/attendance_list.html', {
        'attendance': attendance,
        'today_attendance': today_attendance
    })

@login_required
@role_required(["hr", "super_admin", "director"])
def clock_in(request):
    employee = Employee.objects.get(user=request.user)
    today = date.today()

    attendance, created = Attendance.objects.get_or_create(
        employee=employee,
        date=today
    )

    if not attendance.clock_in:
        attendance.clock_in = timezone.now()
        attendance.status = "present"
        attendance.save()

    return redirect('attendance_list')

@login_required
@role_required(["hr", "super_admin", "director"])
def clock_out(request):
    employee = Employee.objects.get(user=request.user)
    today = date.today()

    attendance = Attendance.objects.get(employee=employee, date=today)
    if not attendance.clock_out:
        attendance.clock_out = timezone.now()
        attendance.save()

    return redirect('attendance_list')

# --- LEAVE REQUESTS ---

@login_required
def apply_leave(request):

    employee = Employee.objects.filter(
        user=request.user
    ).first()

    if not employee:
        return render(
            request,
            'hr/no_employee.html'
        )

    if request.method == "POST":

        start_date = request.POST['start_date']
        end_date = request.POST['end_date']

        if start_date > end_date:

            return render(
                request,
                'hr/apply_leave.html',
                {
                    'error':
                    'End date cannot be earlier than start date.'
                }
            )

        LeaveRequest.objects.create(
            employee=employee,
            leave_type=request.POST['leave_type'],
            start_date=start_date,
            end_date=end_date,
            reason=request.POST['reason']
        )

        messages.success(
            request,
            "Leave request submitted successfully and is awaiting HR approval."
        )

        return redirect('my_leave_history')

    return render(
        request,
        'hr/apply_leave.html'
    )
@login_required
@role_required(["hr", "super_admin", "director"])
def leave_list(request):
    leaves = LeaveRequest.objects.all().order_by('-applied_on')
    return render(request, 'hr/leave_list.html', {'leaves': leaves})

@login_required
@role_required(["hr", "super_admin", "director"])
def update_leave_status(request, leave_id, status):
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    if status in ['approved', 'rejected']:
        leave.status = status
        leave.save()
    return redirect('leave_list')

@login_required
def my_leave_requests(request):

    employee = Employee.objects.filter(
        user=request.user
    ).first()

    leaves = LeaveRequest.objects.filter(
        employee=employee
    ).order_by('-applied_on')

    return render(
        request,
        'hr/my_leave_requests.html',
        {'leaves': leaves}
    )
@login_required
def my_leave_history(request):

    employee = Employee.objects.filter(
        user=request.user
    ).first()

    if not employee:
        return render(request, 'hr/no_employee.html')

    leaves = LeaveRequest.objects.filter(
        employee=employee
    ).order_by('-applied_on')

    return render(
        request,
        'hr/my_leave_history.html',
        {
            'leaves': leaves
        }
    )
@login_required
def salary_advance_request(request):

    employee = Employee.objects.filter(
        user=request.user
    ).first()

    if not employee:
        return render(request, 'hr/no_employee.html')

    if request.method == "POST":

        SalaryAdvance.objects.create(
            employee=employee,
            amount=request.POST['amount'],
            reason=request.POST['reason']
        )

        return redirect('collector_dashboard')

    return render(
        request,
        'hr/salary_advance_request.html'
    )

@login_required
def my_salary_advances(request):

    employee = Employee.objects.filter(
        user=request.user
    ).first()

    if not employee:
        return render(request, 'hr/no_employee.html')

    advances = SalaryAdvance.objects.filter(
        employee=employee
    ).order_by('-requested_on')

    return render(
        request,
        'hr/my_salary_advances.html',
        {
            'advances': advances
        }
    )
@login_required
@role_required(["hr","director","super_admin"])
def salary_advance_list(request):

    advances = SalaryAdvance.objects.all().order_by(
        '-applied_on'
    )

    return render(
        request,
        'hr/salary_advance_list.html',
        {'advances': advances}
    )

# --- PAYROLL MANAGEMENT ---

@login_required
@role_required(["hr", "super_admin", "director"])
def payroll_list(request):
    payrolls = Payroll.objects.all().order_by('-generated_at')
    return render(request, 'hr/payroll_list.html', {'payrolls': payrolls})

@login_required
@role_required(["hr", "super_admin", "director"])
def generate_payroll(request):

    current_month = date.today().strftime("%B %Y")

    employees = Employee.objects.filter(
        status='active'
    )

    created_count = 0

    for emp in employees:

        exists = Payroll.objects.filter(
            employee=emp,
            payroll_month=current_month
        ).exists()

        if not exists:

            Payroll.objects.create(
                employee=emp,
                payroll_month=current_month,
                basic_salary=emp.basic_salary
            )

            created_count += 1

    return redirect('payroll_list')

@login_required
@role_required(["hr", "super_admin", "director"])
def add_payroll(request):
    employees = Employee.objects.all()

    if request.method == "POST":
        employee = get_object_or_404(Employee, id=request.POST['employee'])
        
        # Casting values explicitly to safe floats/Decimals to completely avoid TypeErrors
        Payroll.objects.create(
            employee=employee,
            payroll_month=request.POST['payroll_month'],
            basic_salary=Decimal(request.POST.get('basic_salary', 0)),
            allowances=Decimal(request.POST.get('allowances', 0)),
            deductions=Decimal(request.POST.get('deductions', 0)),
        )
        return redirect('payroll_list')

    return render(request, 'hr/add_payroll.html', {'employees': employees})

@login_required
@role_required(["hr", "super_admin", "director"])
def payroll_detail(request, payroll_id):
    payroll = get_object_or_404(Payroll, id=payroll_id)
    return render(request, 'hr/payroll_detail.html', {'payroll': payroll})