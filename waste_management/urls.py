from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # DASHBOARDS (TOP PRIORITY)
    # =========================
    path('collector/', views.collector_dashboard, name='collector_dashboard'),
    
    
    path('', views.waste_dashboard, name='waste_dashboard'),

    # =========================
    # WASTE OPERATIONS
    # =========================
    path('intake/', views.waste_intake, name='waste_intake'),
    path('list/', views.waste_list, name='waste_list'),
    path('purchase/', views.waste_purchase, name='waste_purchase'),
    path('purchase/<int:purchase_id>/', views.purchase_detail, name='purchase_detail'),
    path('supplier/add/', views.add_supplier, name='add_supplier'),
    path('purchase/<int:purchase_id>/receipt/', views.download_receipt, name='download_receipt'),
    path('purchase/', views.waste_purchase, name='waste_purchase'),
    

    # =========================
    # AJAX / API ACTIONS
    # =========================
    path('ajax/update-status/', views.update_status_ajax, name='update_status_ajax'),

    # =========================
    # STATUS MANAGEMENT
    # =========================
    path(
        'status/<int:waste_id>/<str:status>/',
        views.change_waste_status,
        name='change_waste_status'
    ),

    path(
        'history/<int:waste_id>/',
        views.waste_status_history,
        name='waste_status_history'
    ),
]