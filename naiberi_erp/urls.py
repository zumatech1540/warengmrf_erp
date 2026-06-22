from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from waste_management import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('', include('accounts.urls')),
    path('hr/', include('hr.urls')),
    path('inventory/', include('inventory.urls')),
    path('waste/', include('waste_management.urls')),
    path('finance/', include('finance.urls')),
    path('sales/', include('sales.urls')),
    path('collector/', views.collector_dashboard, name='collector_dashboard'),
    
    # FIX: Point the reports base URL directly to inventory.urls 
    # where your reports_hub is waiting at the root!
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)