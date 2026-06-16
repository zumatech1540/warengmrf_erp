from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db import transaction
from collections import defaultdict
from datetime import timedelta, date

from .models import (
    Item,
    StockMovement,
    SalesOrder,
    SalesOrderItem,
    Supplier,
    PurchaseOrder,
    AccountReceivable
)

import uuid


# -------------------------
# INVENTORY DASHBOARD
# -------------------------
@login_required
def inventory_home(request):
    items = Item.objects.all()

    total_items = items.count()
    total_stock = sum([item.current_stock for item in items])

    return render(request, 'inventory/home.html', {
        'items': items,
        'total_items': total_items,
        'total_stock': total_stock
    })




def item_list(request):
    items = Item.objects.all()
    return render(request, 'inventory/item_list.html', {'items': items})

@login_required
@login_required
def inventory_dashboard(request):

    total_items = Item.objects.count()

    items = Item.objects.all()

    total_stock_value = Item.objects.aggregate(
        total=Sum(F('current_stock'))
    )['total'] or 0

    # FIX: stock value (real ERP calculation)
    total_stock_amount = sum(
        (i.current_stock or 0) * (i.unit_price or 0)
        for i in items
    )

    stock_in = StockMovement.objects.filter(movement_type='in').count()
    stock_out = StockMovement.objects.filter(movement_type='out').count()

    low_stock_items = Item.objects.filter(current_stock__lte=10)

    recent_movements = StockMovement.objects.select_related('item') \
        .order_by('-created_at')[:10]

    top_items = Item.objects.order_by('-current_stock')[:5]

    # CATEGORY SUMMARY (FIXED)
    category_summary = []

    categories = Item.objects.values('category').distinct()

    for cat in categories:
        cat_items = Item.objects.filter(category=cat['category'])

        stock = sum(i.current_stock or 0 for i in cat_items)
        value = sum((i.current_stock or 0) * (i.unit_price or 0) for i in cat_items)

        category_summary.append({
            "name": cat['category'],
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
# -------------------------
# ADD ITEM
# -------------------------
@login_required
def add_item(request):

    if request.method == "POST":
        name = request.POST['name']
        description = request.POST['description']
        unit = request.POST['unit']

        Item.objects.create(
            name=name,
            description=description,
            unit=unit
        )

        return redirect('inventory_home')

    return render(request, 'inventory/add_item.html')


# -------------------------
# STOCK PAGE
# -------------------------
@login_required
def stock_page(request):
    movements = StockMovement.objects.all().order_by('-created_at')

    return render(request, 'inventory/stock.html', {
        'movements': movements
    })

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
@login_required
def po_list(request):

    pos = PurchaseOrder.objects.all().order_by('-created_at')

    return render(request, 'inventory/po_list.html', {
        'pos': pos
    })

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

    return render(request, 'inventory/po_detail.html', {
        'po': po,
        'items': items
    })

@login_required
def receive_po(request, po_id):

    po = PurchaseOrder.objects.get(id=po_id)
    po.receive_order()

    return redirect('po_detail', po_id=po.id)



@login_required
def run_auto_reorder(request):

    po = generate_auto_purchase_orders(user=request.user)

    if po:
        return redirect('po_detail', po_id=po.id)
    else:
        return redirect('reorder_dashboard')


@login_required
def reorder_dashboard(request):

    low_stock_items = Item.objects.filter(
        current_stock__lte=F('reorder_level')
    )

    all_items = Item.objects.all()

    return render(request, 'inventory/reorder_dashboard.html', {
        'low_stock_items': low_stock_items,
        'all_items': all_items
    })




@login_required
def forecast_dashboard(request):

    items = Item.objects.all()

    forecasts = []

    for item in items:
        forecasts.append(forecast_item_demand(item))

    # Sort by urgency (lowest days remaining first)
    forecasts = sorted(
        forecasts,
        key=lambda x: x['days_remaining']
    )

    return render(request, 'inventory/forecast_dashboard.html', {
        'forecasts': forecasts
    })





@login_required
def category_dashboard(request):

    items = Item.objects.all()

    summary = {}

    for item in items:
        cat = item.category

        if cat not in summary:
            summary[cat] = {
                'stock': 0,
                'value': 0,
                'count': 0
            }

        summary[cat]['stock'] += float(item.current_stock)
        summary[cat]['value'] += float(item.current_stock * item.unit_price)
        summary[cat]['count'] += 1

    # =========================
    # CHART DATA PREPARATION
    # =========================
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

    # =========================
    # FILTERS
    # =========================
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

    # =========================
    # CATEGORY SUMMARY
    # =========================
    summary = defaultdict(lambda: {
        'revenue': 0,
        'cost': 0,
        'profit': 0
    })

    # =========================
    # DAILY TRENDS
    # =========================
    daily = defaultdict(lambda: {
        'revenue': 0,
        'cost': 0,
        'profit': 0
    })

    for i in items:

        cat = i.item.category
        date = i.sales_order.order_date.date()

        revenue = float(i.total)
        cost = float(i.quantity * i.item.unit_price)
        profit = revenue - cost

        # CATEGORY
        summary[cat]['revenue'] += revenue
        summary[cat]['cost'] += cost
        summary[cat]['profit'] += profit

        # DAILY
        daily[str(date)]['revenue'] += revenue
        daily[str(date)]['cost'] += cost
        daily[str(date)]['profit'] += profit

    # =========================
    # CHART DATA
    # =========================
    categories = list(summary.keys())

    revenue_data = [summary[c]['revenue'] for c in categories]
    cost_data = [summary[c]['cost'] for c in categories]
    profit_data = [summary[c]['profit'] for c in categories]

    dates = sorted(daily.keys())

    revenue_trend = [daily[d]['revenue'] for d in dates]
    cost_trend = [daily[d]['cost'] for d in dates]
    profit_trend = [daily[d]['profit'] for d in dates]

    return render(request, "inventory/profit_dashboard.html", {
        "summary": summary,
        "categories": categories,
        "revenue_data": revenue_data,
        "cost_data": cost_data,
        "profit_data": profit_data,

        # trends
        "dates": dates,
        "revenue_trend": revenue_trend,
        "cost_trend": cost_trend,
        "profit_trend": profit_trend,

        "period": period,
    })




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

    return render(request, 'sales/sales_list.html', {
        'orders': orders
    })

def sales_detail(request, order_id):

    order = SalesOrder.objects.get(id=order_id)

    return render(request, 'sales/sales_detail.html', {
        'order': order
    })

from django.shortcuts import render
from django.db.models import Sum
from .models import AccountReceivable


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

from datetime import timedelta, date


def ar_aging_report(request):

    ars = AccountReceivable.objects.all()

    today = date.today()

    bucket_0_30 = []
    bucket_31_60 = []
    bucket_61_90 = []
    bucket_90_plus = []

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

from collections import defaultdict

def category_profit(request):

    data = defaultdict(lambda: {"revenue": 0, "cost": 0})

    items = SalesOrderItem.objects.select_related('item')

    for i in items:
        cat = i.item.category

        revenue = i.total
        cost = i.quantity * i.item.unit_price

        data[cat]["revenue"] += revenue
        data[cat]["cost"] += cost

    for k in data:
        data[k]["profit"] = data[k]["revenue"] - data[k]["cost"]

    return render(request, 'finance/category_profit.html', {
        'data': data
    })



def stock_movement_list(request):
    movements = StockMovement.objects.select_related('item').all().order_by('-created_at')

    return render(request, 'inventory/stock_movements.html', {
        'movements': movements
    })