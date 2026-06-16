from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from .models import Sale, Customer
from inventory.models import Item




# =========================
# SALES DASHBOARD
# =========================
@login_required
def sales_dashboard(request):

    sales = Sale.objects.all().order_by('-created_at')

    total_sales = sales.count()

    total_revenue = sum(
        sale.total_amount for sale in sales
    )

    return render(
        request,
        'sales/dashboard.html',
        {
            'sales': sales,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
        }
    )


# =========================
# CREATE SALE
# =========================
@login_required
def create_sale(request):

    customers = Customer.objects.all()
    items = Item.objects.all()

    error = None

    if request.method == "POST":

        try:

            Sale.objects.create(
                customer_id=request.POST['customer'],
                item_id=request.POST['item'],
                quantity=request.POST['quantity'],
                unit_price=request.POST['unit_price'],
                created_by=request.user
            )

            return redirect('sales_dashboard')

        except Exception as e:
            error = str(e)

    return render(
        request,
        'sales/create_sale.html',
        {
            'customers': customers,
            'items': items,
            'error': error,
        }
    )


# =========================
# SALES LIST
# =========================
@login_required
def sale_list(request):

    sales = Sale.objects.all().order_by('-created_at')

    return render(
        request,
        'sales/sale_list.html',
        {'sales': sales}
    )

@login_required
def sale_invoice(request, sale_id):

    sale = get_object_or_404(Sale, id=sale_id)

    return render(
        request,
        'sales/invoice.html',
        {'sale': sale}
    )