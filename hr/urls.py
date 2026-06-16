from django.urls import path
from . import views

urlpatterns = [

    path('', views.hr_dashboard, name='hr_dashboard'),

    # ================= EMPLOYEES =================
    path('employees/', views.employee_list, name='employee_list'),

    path('employees/add/', views.add_employee, name='add_employee'),

    path('employees/edit/<int:employee_id>/', views.edit_employee, name='edit_employee'),

    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),

    # ================= ATTENDANCE =================
    path('attendance/', views.attendance_list, name='attendance_list'),

    path('attendance/mark/<int:employee_id>/', views.mark_attendance, name='mark_attendance'),

    # ================= LEAVE =================
    path('leave/', views.leave_list, name='leave_list'),

    path('leave/apply/', views.apply_leave, name='apply_leave'),
    

    path('leave/update/<int:leave_id>/<str:status>/', views.update_leave_status, name='update_leave_status'),

    # ================= PAYROLL =================
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/add/', views.add_payroll, name='add_payroll'),

    path('payroll/generate/', views.generate_payroll, name='generate_payroll'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/clock-in/', views.clock_in, name='clock_in'),
    path('attendance/clock-out/', views.clock_out, name='clock_out'),
]