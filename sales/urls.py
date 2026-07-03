from django.urls import path
from . import views

urlpatterns = [

    path(
        '',
        views.sales_dashboard,
        name='sales_dashboard'
    ),

    path(
        'create/',
        views.create_sale,
        name='create_sale'
    ),
    path('list/', views.sale_list, name='sale_list'),
    path('invoice/<int:sale_id>/', views.sale_invoice, name='sale_invoice'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('invoice/<int:sale_id>/pdf/', views.sale_invoice_pdf, name='sale_invoice_pdf'
),

path(
    'invoices/',
    views.invoice_list,
    name='invoice_list'
),
path(
    'invoice/<int:invoice_id>/pdf/',
    views.invoice_pdf_view,
    name='invoice_pdf'
),

]