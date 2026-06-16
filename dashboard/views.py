import json
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.db.models import Sum

from inventory.models import Item, StockMovement
from waste_management.models import WasteIntake
from sales.models import Sale

@login_required
def dashboard_home(request):

    today = timezone.now().date()

    # =========================
    # INVENTORY KPIs
    # =========================
    total_items = Item.objects.count()

    total_stock_value = sum(
        float(item.stock_value()) for item in Item.objects.all()
    )

    low_stock_items = Item.objects.filter(
        current_stock__lte=10
    ).count()

    # =========================
    # WASTE KPIs
    # =========================
    waste_today = WasteIntake.objects.filter(
        created_at__date=today
    ).count()

    # =========================
    # SALES KPIs
    # =========================
    total_sales = Sale.objects.count()

    sales_today = Sale.objects.filter(
        created_at__date=today
    ).count()

    # =========================
    # PROCUREMENT / STOCK MOVEMENTS
    # =========================
    purchases_today = StockMovement.objects.filter(
        movement_type='in',
        created_at__date=today
    ).count()

    stock_in = StockMovement.objects.filter(
        movement_type='in'
    ).count()

    stock_out = StockMovement.objects.filter(
        movement_type='out'
    ).count()

    # =========================
    # CHART DATA (7 DAYS TREND)
    # =========================
    sales_labels = []
    sales_data = []

    waste_labels = []
    waste_data = []

    for i in range(6, -1, -1):

        day = today - timedelta(days=i)

        # sales trend
        sales_count = Sale.objects.filter(
            created_at__date=day
        ).count()

        sales_labels.append(day.strftime("%d %b"))
        sales_data.append(sales_count)

        # waste trend
        waste_count = WasteIntake.objects.filter(
            created_at__date=day
        ).count()

        waste_labels.append(day.strftime("%d %b"))
        waste_data.append(waste_count)

    # =========================
    # TOP INVENTORY ITEMS
    # =========================
    items = Item.objects.order_by('-current_stock')[:5]

    item_labels = [item.name for item in items]
    item_stock = [float(item.current_stock) for item in items]

    # =========================
    # CONTEXT
    # =========================
    context = {

        # INVENTORY
        "total_items": total_items,
        "total_stock_value": total_stock_value,
        "low_stock_items": low_stock_items,

        # WASTE
        "waste_today": waste_today,

        # SALES
        "total_sales": total_sales,
        "sales_today": sales_today,

        # STOCK MOVEMENTS
        "purchases_today": purchases_today,
        "stock_in": stock_in,
        "stock_out": stock_out,

        # CHARTS
        "sales_labels": json.dumps(sales_labels),
        "sales_data": json.dumps(sales_data),

        "waste_labels": json.dumps(waste_labels),
        "waste_data": json.dumps(waste_data),

        "item_labels": json.dumps(item_labels),
        "item_stock": json.dumps(item_stock),
    }

    return render(request, "dashboard/dashboard.html", context)