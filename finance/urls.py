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
    path(
    'customer-payment/<int:sale_id>/',
    views.receive_customer_payment,
    name='receive_customer_payment'
    ),
path(
    'customer-payments/',
    views.customer_payment_list,
    name='customer_payment_list'
),
path(
    'journals/',
    views.journal_list,
    name='journal_list'
),
path(
    'waste-receipts/',
    views.waste_receipt_list,
    name='waste_receipt_list'
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
path('ledger/', views.ledger_list, name='ledger_list'),
path('reports/', views.financial_reports, name='financial_reports'),
path('reports/export/<str:report_type>/', views.export_report_pdf, name='export_report_pdf'),
path('invoices/', views.invoice_list, name='invoice_list'),
]