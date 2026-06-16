from django.urls import path
from . import views

urlpatterns = [
    path('', views.waste_dashboard, name='waste_dashboard'),
    path('intake/', views.waste_intake, name='waste_intake'),
    path('list/', views.waste_list, name='waste_list'),
    path('ajax/update-status/', views.update_status_ajax, name='update_status_ajax'),
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