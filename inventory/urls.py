from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_home, name='inventory_home'),
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('add-item/', views.add_item, name='add_item'),
    path('stock/', views.stock_page, name='stock_page'),
    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/add/', views.add_po, name='add_po'),
    path('purchase-orders/<int:po_id>/', views.po_detail, name='po_detail'),
    path('purchase-orders/receive/<int:po_id>/', views.receive_po, name='receive_po'),
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('reorder/', views.reorder_dashboard, name='reorder_dashboard'),

    # AUTO PO
    path('reorder/run/', views.run_auto_reorder, name='run_auto_reorder'),
    path('forecast/', views.forecast_dashboard, name='forecast_dashboard'),
    path('categories/', views.category_dashboard, name='category_dashboard'),
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.add_item, name='add_item'),
    path('movements/', views.stock_movement_list, name='stock_movements'),
]