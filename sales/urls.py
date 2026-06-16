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

]