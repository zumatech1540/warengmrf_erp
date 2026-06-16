from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required


# -------------------------
# LOGIN VIEW
# -------------------------
def login_view(request):

    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    if request.method == "POST":

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard_redirect')

        return render(request, 'accounts/login.html', {
            'error': 'Invalid username or password'
        })

    return render(request, 'accounts/login.html')


# -------------------------
# LOGOUT
# -------------------------
def logout_view(request):
    logout(request)
    return redirect('login')


# -------------------------
# DASHBOARD REDIRECT ENGINE (ERP CORE)
# -------------------------
@login_required
def dashboard_redirect(request):

    role = request.user.role

    routing = {
        "super_admin": "/dashboard/",

        "managing_director": "/dashboard/executive/",

        "operations_manager": "/dashboard/operations/",

        "finance_manager": "/finance/",

        "hr_manager": "/hr/",

        "inventory_officer": "/inventory/",

        "collection_officer": "/waste/",

        "data_entry_clerk": "/dashboard/data-entry/",

        "viewer": "/dashboard/",  
    }

    return redirect(routing.get(role, "/dashboard/"))

# -------------------------
# DEFAULT DASHBOARD
# -------------------------
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')