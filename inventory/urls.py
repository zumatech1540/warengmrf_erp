from django.urls import path
from . import views

urlpatterns = [
    # =========================
    # INVENTORY APP BASE PATHS
    # =========================
    # This empty string now safely belongs to Inventory Home again!
    path('', views.inventory_home, name='inventory_home'), 
    path('dashboard/', views.inventory_dashboard, name='inventory_dashboard'),
    path('reorder/', views.reorder_dashboard, name='reorder_dashboard'),
    path('categories/', views.category_dashboard, name='category_dashboard'),

    # =========================
    # CENTRALIZED BUSINESS REPORTS (Isolated Prefixes)
    # =========================
    path('hub/', views.reports_hub, name='reports_hub'),
    path('profit/', views.profit_by_category, name='report_profit'),
    path('aging/', views.ar_aging_report, name='report_aging'),
    path('forecast/', views.forecast_dashboard, name='report_forecast'),

    # =========================
    # ITEMS & STOCK MANAGEMENT
    # =========================
    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.add_item, name='add_item'),
    path('stock/', views.stock_page, name='stock_page'),
    path('movements/', views.stock_movement_list, name='stock_movements'),

    # =========================
    # PROCUREMENT (PURCHASE ORDERS)
    # =========================
    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/add/', views.add_po, name='add_po'),
    path('purchase-orders/<int:po_id>/', views.po_detail, name='po_detail'),
    path('purchase-orders/receive/<int:po_id>/', views.receive_po, name='receive_po'),
    path('reorder/run/', views.run_auto_reorder, name='run_auto_reorder'),

    # =========================
    # PARTNERS (SUPPLIERS & CUSTOMERS)
    # =========================
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    path('suppliers/<int:supplier_id>/', views.supplier_detail, name='supplier_detail'),
    
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
]