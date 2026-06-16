from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Employee, Attendance, LeaveRequest, Payroll
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import LeaveRequest, Employee, Attendance, Payroll
from django.utils import timezone
from datetime import date

@login_required
def hr_home(request):
    return render(request, 'hr/hr_home.html')

@login_required
def hr_dashboard(request):

    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status='active').count()
    inactive_employees = Employee.objects.filter(status='inactive').count()
    terminated_employees = Employee.objects.filter(status='terminated').count()

    pending_leaves = LeaveRequest.objects.filter(status='pending').count()
    approved_leaves = LeaveRequest.objects.filter(status='approved').count()
    rejected_leaves = LeaveRequest.objects.filter(status='rejected').count()

    # Attendance placeholders (we will improve later)
    present_today = Attendance.objects.filter(date=date.today(), clock_in__isnull=False).count()
    absent_today = total_employees - present_today
    late_today = 0  # upgrade later with rules

    return render(request, 'hr/dashboard.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'terminated_employees': terminated_employees,
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
    })

@login_required
def employee_list(request):
    employees = Employee.objects.all().order_by('-created_at')

    return render(request, 'hr/employee_list.html', {
        'employees': employees
    })

@login_required
def add_employee(request):

    if request.method == "POST":

        Employee.objects.create(
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            employee_number=request.POST['employee_number'],
            email=request.POST.get('email', ''),
            phone=request.POST['phone'],
            position=request.POST['position'],
            department_id=request.POST['department'],
            hire_date=request.POST['hire_date'],
            basic_salary=request.POST['basic_salary'],
            address=request.POST.get('address', ''),
            emergency_contact_name=request.POST.get('emergency_contact_name', ''),
            emergency_contact_phone=request.POST.get('emergency_contact_phone', '')
        )

        return redirect('employee_list')

    return render(request, 'hr/add_employee.html')

@login_required
def edit_employee(request, employee_id):

    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == "POST":

        employee.first_name = request.POST['first_name']
        employee.last_name = request.POST['last_name']
        employee.phone = request.POST['phone']
        employee.position = request.POST['position']
        employee.basic_salary = request.POST['basic_salary']
        employee.status = request.POST['status']

        employee.save()

        return redirect('employee_list')

    return render(request, 'hr/edit_employee.html', {
        'employee': employee
    })

@login_required
def employee_detail(request, employee_id):

    employee = get_object_or_404(Employee, id=employee_id)

    return render(request, 'hr/employee_detail.html', {
        'employee': employee
    })

@login_required
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
def attendance_list(request):

    attendance = Attendance.objects.all().order_by('-date')

    return render(request, 'hr/attendance_list.html', {
        'attendance': attendance
    })



@login_required
def apply_leave(request):

    employee = Employee.objects.filter(user=request.user).first()

    if not employee:
        return render(request, 'hr/no_employee.html')

    if request.method == "POST":

        LeaveRequest.objects.create(
            employee=employee,
            leave_type=request.POST['leave_type'],
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date'],
            reason=request.POST['reason']
        )

        return redirect('leave_list')

    return render(request, 'hr/apply_leave.html')
@login_required
def leave_list(request):

    leaves = LeaveRequest.objects.all().order_by('-applied_on')

    return render(request, 'hr/leave_list.html', {
        'leaves': leaves
    })

@login_required
def update_leave_status(request, leave_id, status):

    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if status in ['approved', 'rejected']:
        leave.status = status
        leave.save()

    return redirect('leave_list')

@login_required
def payroll_list(request):

    payrolls = Payroll.objects.all().order_by('-generated_at')

    return render(request, 'hr/payroll_list.html', {
        'payrolls': payrolls
    })

@login_required
def generate_payroll(request):

    employees = Employee.objects.filter(status='active')

    for emp in employees:

        Payroll.objects.create(
            employee=emp,
            payroll_month=date.today().strftime("%B %Y"),
            basic_salary=emp.basic_salary
        )

    return redirect('payroll_list')
@login_required
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
def clock_out(request):

    employee = Employee.objects.get(user=request.user)

    today = date.today()

    attendance = Attendance.objects.get(employee=employee, date=today)

    if not attendance.clock_out:
        attendance.clock_out = timezone.now()
        attendance.save()

    return redirect('attendance_list')

@login_required
def attendance_list(request):

    employee = Employee.objects.get(user=request.user)

    attendance = Attendance.objects.filter(employee=employee).order_by('-date')

    today_attendance = Attendance.objects.filter(
        employee=employee,
        date=date.today()
    ).first()

    return render(request, 'hr/attendance_list.html', {
        'attendance': attendance,
        'today_attendance': today_attendance
    })



@login_required
def attendance_list(request):

    employee = Employee.objects.filter(user=request.user).first()

    if not employee:
        return render(request, 'hr/no_employee.html')

    attendance = Attendance.objects.filter(employee=employee).order_by('-date')

    today_attendance = Attendance.objects.filter(
        employee=employee,
        date=date.today()
    ).first()

    return render(request, 'hr/attendance_list.html', {
        'attendance': attendance,
        'today_attendance': today_attendance
    })





@login_required
def add_payroll(request):

    employees = Employee.objects.all()

    if request.method == "POST":

        employee = get_object_or_404(Employee, id=request.POST['employee'])

        payroll = Payroll.objects.create(
            employee=employee,
            payroll_month=request.POST['payroll_month'],
            basic_salary=request.POST['basic_salary'],
            allowances=request.POST.get('allowances', 0),
            deductions=request.POST.get('deductions', 0),
        )

        return redirect('payroll_list')

    return render(request, 'hr/add_payroll.html', {
        'employees': employees
    })
