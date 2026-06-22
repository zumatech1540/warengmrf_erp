import uuid
from datetime import timedelta, date
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db import transaction
from django.http import HttpResponse
from core.models import Supplier
from django.utils.timezone import now

from accounts.decorators import role_required
from .models import (
    Item,
    StockMovement,
    SalesOrder,
    SalesOrderItem,
   
    PurchaseOrder,
    AccountReceivable
)
from sales.models import Customer, Sale  # Ensure correct cross-app import path

# =========================================================================
# HELPER MOCK FUNCTIONS
# =========================================================================
def generate_auto_purchase_orders(user):
    """
    Fallback placeholder function to prevent NameError.
    Replace or point this to your actual automation utils engine if applicable!
    """
    return None

# =========================================================================
# 1. INVENTORY CORE & DASHBOARDS
# =========================================================================

@login_required
@role_required(["inventory", "super_admin", "director"])
def inventory_home(request):
    items = Item.objects.all()
    total_items = items.count()
    total_stock = sum([item.current_stock for item in items])

    return render(request, 'inventory/home.html', {
        'items': items,
        'total_items': total_items,
        'total_stock': total_stock
    })

@login_required
@role_required(["inventory", "super_admin", "director"])
def inventory_dashboard(request):
    total_items = Item.objects.count()
    items = Item.objects.all()

    total_stock_value = Item.objects.aggregate(
        total=Sum(F('current_stock'))
    )['total'] or 0

    total_stock_amount = sum(
        (i.current_stock or 0) * (i.unit_price or 0)
        for i in items
    )

    stock_in = StockMovement.objects.filter(movement_type='in').count()
    stock_out = StockMovement.objects.filter(movement_type='out').count()
    low_stock_items = Item.objects.filter(current_stock__lte=10)

    recent_movements = StockMovement.objects.select_related('item').order_by('-created_at')[:10]
    top_items = Item.objects.order_by('-current_stock')[:5]

    category_summary = []
    categories = Item.objects.values('category').distinct()

    for cat in categories:
        cat_name = cat['category'] if cat['category'] else "Uncategorized"
        cat_items = Item.objects.filter(category=cat['category'])
        stock = sum(i.current_stock or 0 for i in cat_items)
        value = sum((i.current_stock or 0) * (i.unit_price or 0) for i in cat_items)

        category_summary.append({
            "name": cat_name,
            "stock": stock,
            "value": value
        })

    return render(request, 'inventory/dashboard.html', {
        'total_items': total_items,
        'total_stock_value': total_stock_value,
        'total_stock_amount': total_stock_amount,
        'stock_in': stock_in,
        'stock_out': stock_out,
        'low_stock_items': low_stock_items,
        'recent_movements': recent_movements,
        'top_items': top_items,
        'category_summary': category_summary,
    })

def item_list(request):
    items = Item.objects.all()
    return render(request, 'inventory/item_list.html', {'items': items})

@login_required
def add_item(request):
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        unit = request.POST.get('unit')

        Item.objects.create(
            name=name,
            description=description,
            unit=unit
        )
        return redirect('inventory_home')

    return render(request, 'inventory/add_item.html', {'suppliers': suppliers})

# =========================================================================
# 2. STOCK MOVEMENTS
# =========================================================================

@login_required
def stock_page(request):
    items = Item.objects.all()

    if request.method == "POST":
        item_id = request.POST['item']
        movement_type = request.POST['movement_type']
        quantity = float(request.POST['quantity'])
        reason = request.POST.get('reason')

        item = Item.objects.get(id=item_id)

        StockMovement.objects.create(
            item=item,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            created_by=request.user
        )
        return redirect('stock_page')

    movements = StockMovement.objects.all().order_by('-created_at')
    return render(request, 'inventory/stock.html', {
        'items': items,
        'movements': movements
    })

def stock_movement_list(request):
    movements = StockMovement.objects.select_related('item').all().order_by('-created_at')
    return render(request, 'inventory/stock_movements.html', {'movements': movements})

# =========================================================================
# 3. PROCUREMENT & PURCHASING (PO)
# =========================================================================

@login_required
def po_list(request):
    pos = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, 'inventory/po_list.html', {'pos': pos})

@login_required
def add_po(request):
    suppliers = Supplier.objects.all()
    items = Item.objects.all()

    if request.method == "POST":
        supplier = Supplier.objects.get(id=request.POST['supplier'])
        po = PurchaseOrder.objects.create(
            po_number=request.POST['po_number'],
            supplier=supplier,
            created_by=request.user
        )
        return redirect('po_detail', po_id=po.id)

    return render(request, 'inventory/add_po.html', {
        'suppliers': suppliers,
        'items': items
    })

@login_required
def po_detail(request, po_id):
    po = PurchaseOrder.objects.get(id=po_id)
    items = po.items.all()
    return render(request, 'inventory/po_detail.html', {'po': po, 'items': items})

@login_required
def receive_po(request, po_id):
    po = PurchaseOrder.objects.get(id=po_id)
    po.receive_order()
    return redirect('po_detail', po_id=po.id)

@login_required
def reorder_dashboard(request):
    low_stock_items = Item.objects.filter(current_stock__lte=F('reorder_level'))
    all_items = Item.objects.all()
    return render(request, 'inventory/reorder_dashboard.html', {
        'low_stock_items': low_stock_items,
        'all_items': all_items
    })

# =========================================================================
# 4. BUSINESS INTEGRATION, DEMAND FORECASTING & ANALYSIS
# =========================================================================

@login_required
def forecast_dashboard(request):
    items = Item.objects.all()
    forecasts = []
    
    for item in items:
        forecasts.append({
            'item': item,
            'days_remaining': 30  
        })

    forecasts = sorted(forecasts, key=lambda x: x['days_remaining'])
    return render(request, 'inventory/forecast_dashboard.html', {'forecasts': forecasts})

@login_required
def category_dashboard(request):
    items = Item.objects.all()
    summary = {}

    for item in items:
        cat = item.category if item.category else "Uncategorized"
        if cat not in summary:
            summary[cat] = {'stock': 0, 'value': 0, 'count': 0}

        summary[cat]['stock'] += float(item.current_stock or 0)
        summary[cat]['value'] += float((item.current_stock or 0) * (item.unit_price or 0))
        summary[cat]['count'] += 1

    categories = list(summary.keys())
    stock_data = [summary[c]['stock'] for c in categories]
    value_data = [summary[c]['value'] for c in categories]
    count_data = [summary[c]['count'] for c in categories]

    return render(request, 'inventory/category_dashboard.html', {
        'summary': summary,
        'categories': categories,
        'stock_data': stock_data,
        'value_data': value_data,
        'count_data': count_data,
    })

@login_required
def profit_by_category(request):
    period = request.GET.get("period", "month")
    today = now().date()

    if period == "today":
        start_date = today
    elif period == "week":
        start_date = today - timedelta(days=7)
    elif period == "month":
        start_date = today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=365)

    items = SalesOrderItem.objects.filter(
        sales_order__order_date__date__gte=start_date
    ).select_related('item')

    summary = defaultdict(lambda: {'revenue': 0, 'cost': 0, 'profit': 0})
    daily = defaultdict(lambda: {'revenue': 0, 'cost': 0, 'profit': 0})

    for i in items:
        cat = i.item.category if i.item.category else "Uncategorized"
        item_date = i.sales_order.order_date.date()

        revenue = float(i.total or 0)
        cost = float((i.quantity or 0) * (i.item.unit_price or 0))
        profit = revenue - cost

        summary[cat]['revenue'] += revenue
        summary[cat]['cost'] += cost
        summary[cat]['profit'] += profit

        daily[str(item_date)]['revenue'] += revenue
        daily[str(item_date)]['cost'] += cost
        daily[str(item_date)]['profit'] += profit

    categories = list(summary.keys())
    revenue_data = [summary[c]['revenue'] for c in categories]
    cost_data = [summary[c]['cost'] for c in categories]
    profit_data = [summary[c]['profit'] for c in categories]

    dates = sorted(daily.keys())
    revenue_trend = [daily[d]['revenue'] for d in dates]
    cost_trend = [daily[d]['cost'] for d in dates]
    profit_trend = [daily[d]['profit'] for d in dates]

    return render(request, "inventory/profit_dashboard.html", {
        "summary": dict(summary),
        "categories": categories,
        "revenue_data": revenue_data,
        "cost_data": cost_data,
        "profit_data": profit_data,
        "dates": dates,
        "revenue_trend": revenue_trend,
        "cost_trend": cost_trend,
        "profit_trend": profit_trend,
        "period": period,
    })

# =========================================================================
# 5. SALES & RETAIL INTERFACES
# =========================================================================

def create_sales_order(request):
    if request.method == "POST":
        with transaction.atomic():
            customer_id = request.POST['customer']
            items = request.POST.getlist('item')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('price')

            order = SalesOrder.objects.create(
                customer_id=customer_id,
                order_number=str(uuid.uuid4())[:10],
                created_by=request.user
            )

            for i in range(len(items)):
                SalesOrderItem.objects.create(
                    sales_order=order,
                    item_id=items[i],
                    quantity=quantities[i],
                    unit_price=prices[i]
                )
        return redirect('sales_list')

    return render(request, 'sales/create_sales.html', {
        'items': Item.objects.all()
    })

def sales_list(request):
    orders = SalesOrder.objects.all().order_by('-id')
    return render(request, 'sales/sales_list.html', {'orders': orders})

def sales_detail(request, order_id):
    order = SalesOrder.objects.get(id=order_id)
    return render(request, 'sales/sales_detail.html', {'order': order})

# =========================================================================
# 6. FINANCE & ACCOUNT RECEIVABLES (AR)
# =========================================================================

def ar_dashboard(request):
    ars = AccountReceivable.objects.all()
    total_ar = ars.aggregate(Sum('balance'))['balance__sum'] or 0
    total_invoices = ars.count()

    paid = ars.filter(status='paid').count()
    partial = ars.filter(status='partial').count()
    unpaid = ars.filter(status='unpaid').count()

    return render(request, 'finance/ar_dashboard.html', {
        'ars': ars,
        'total_ar': total_ar,
        'total_invoices': total_invoices,
        'paid': paid,
        'partial': partial,
        'unpaid': unpaid,
    })

def ar_aging_report(request):
    ars = AccountReceivable.objects.all()
    today = date.today()

    bucket_0_30, bucket_31_60, bucket_61_90, bucket_90_plus = [], [], [], []

    for ar in ars:
        days = (today - ar.created_at.date()).days
        if days <= 30:
            bucket_0_30.append(ar)
        elif days <= 60:
            bucket_31_60.append(ar)
        elif days <= 90:
            bucket_61_90.append(ar)
        else:
            bucket_90_plus.append(ar)

    return render(request, 'finance/ar_aging.html', {
        'bucket_0_30': bucket_0_30,
        'bucket_31_60': bucket_31_60,
        'bucket_61_90': bucket_61_90,
        'bucket_90_plus': bucket_90_plus,
    })

def category_profit(request):
    data = defaultdict(lambda: {"revenue": 0, "cost": 0})
    items = SalesOrderItem.objects.select_related('item')

    for i in items:
        cat = i.item.category if i.item.category else "Uncategorized"
        data[cat]["revenue"] += float(i.total or 0)
        data[cat]["cost"] += float((i.quantity or 0) * (i.item.unit_price or 0))

    for k in data:
        data[k]["profit"] = data[k]["revenue"] - data[k]["cost"]

    # FIX: Cast to regular dict to protect against the template engine .items unpacking bug
    return render(request, 'finance/category_profit.html', {'data': dict(data)})

# =========================================================================
# 7. PARTNERS (SUPPLIERS & CUSTOMERS)
# =========================================================================

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('company_name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def add_supplier(request):
    if request.method == "POST":
        company_name = request.POST.get('name')
        contact_person = request.POST.get('contact_person') or ""
        phone = request.POST.get('phone')
        email = request.POST.get('email') or ""
        address = request.POST.get('address') or ""

        if not company_name:
            return HttpResponse("Supplier name is required", status=400)
        if not phone:
            return HttpResponse("Phone number is required", status=400)

        Supplier.objects.create(
            company_name=company_name,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=address,
        )
        return redirect('supplier_list')

    return render(request, 'inventory/add_supplier.html')

@login_required
def supplier_detail(request, supplier_id):
    supplier = Supplier.objects.get(id=supplier_id)
    return render(request, 'inventory/supplier_detail.html', {'supplier': supplier})

@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('company_name')
    return render(request, 'inventory/customer_list.html', {'customers': customers})

@login_required
def add_customer(request):
    if request.method == "POST":
        Customer.objects.create(
            company_name=request.POST['company_name'],
            contact_person=request.POST.get('contact_person'),
            phone=request.POST['phone'],
            email=request.POST.get('email'),
            address=request.POST.get('address'),
        )
        return redirect('create_sale')

    return render(request, 'inventory/add_customer.html')

@login_required
def customer_detail(request, customer_id):
    customer = Customer.objects.get(id=customer_id)
    return render(request, 'inventory/customer_detail.html', {'customer': customer})

@login_required
def run_auto_reorder(request):
    po = generate_auto_purchase_orders(user=request.user)

    if po:
        return redirect('po_detail', po_id=po.id)
    else:
        return redirect('reorder_dashboard')

@login_required
@role_required(["super_admin", "director", "finance", "inventory"])
def reports_hub(request):
    return render(request, 'inventory/reports_hub.html')