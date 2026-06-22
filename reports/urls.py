from django.urls import path
from . import views

urlpatterns = [
    # Running http://127.0.0.1:8000/reports/ hits this landing layout cleanly!
    path('', views.reports_hub, name='reports_hub'),
    path('profit/', views.profit_by_category, name='report_profit'),
    path('aging/', views.ar_aging_report, name='report_aging'),
    path('forecast/', views.forecast_dashboard, name='report_forecast'),
]