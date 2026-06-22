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

    print("REDIRECT ROLE:", role)

    if role == "super_admin":
        return redirect("/dashboard/")

    if role == "collection":
        return redirect("/waste/collector/")

    if role == "finance":
        return redirect("/finance/")

    if role == "inventory":
        return redirect("/inventory/")

    if role == "hr":
        return redirect("/hr/")

    if role == "manager":
        return redirect("/dashboard/manager/")

    return redirect("/dashboard/")
# -------------------------
# DEFAULT DASHBOARD
# -------------------------
@login_required
def dashboard(request):

    print("ROLE:", request.user.role)  # DEBUG LINE

    if request.user.role != "super_admin":
        return redirect("dashboard_redirect")

    return render(request, "dashboard/erp_home.html")