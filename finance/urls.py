from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.finance_dashboard,
        name='finance_dashboard'
    ),

    path(
        'income/',
        views.income_list,
        name='income_list'
    ),

    path(
        'income/add/',
        views.add_income,
        name='add_income'
    ),

    path(
        'expense/',
        views.expense_list,
        name='expense_list'
    ),

    path(
        'expense/add/',
        views.add_expense,
        name='add_expense'
    ),

# AR (Accounts Receivable)
path('ar/', views.ar_list, name='ar_list'),
path('ar/add/', views.add_ar, name='add_ar'),

# AP (Accounts Payable)
path('ap/', views.ap_list, name='ap_list'),
path('ap/add/', views.add_ap, name='add_ap'),
path('payment/', views.make_payment, name='make_payment'),
path('receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
path('invoice/<int:ar_id>/pdf/', views.invoice_pdf_view, name='invoice_pdf'),
]