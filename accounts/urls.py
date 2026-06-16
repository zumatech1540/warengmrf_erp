from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import login_view, logout_view, dashboard_redirect

urlpatterns = [
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard-redirect/', dashboard_redirect, name='dashboard_redirect'),
]