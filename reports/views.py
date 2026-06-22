from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import timedelta, date
from collections import defaultdict
from django.utils.timezone import now

# Cross-app data tracking imports
from accounts.decorators import role_required
from inventory.models import Item, SalesOrderItem, PurchaseOrder
from finance.models import AccountReceivable

@login_required
@role_required(["super_admin", "director", "finance", "inventory"])
def reports_hub(request):
    return render(request, 'reports/reports_hub.html')

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

    return render(request, "reports/profit_dashboard.html", {
        "summary": dict(summary),
        "period": period,
    })

@login_required
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

    return render(request, 'reports/ar_aging.html', {
        'bucket_0_30': bucket_0_30,
        'bucket_31_60': bucket_31_60,
        'bucket_61_90': bucket_61_90,
        'bucket_90_plus': bucket_90_plus,
    })

@login_required
def forecast_dashboard(request):
    items = Item.objects.all()
    forecasts = [{'item': item, 'days_remaining': 30} for item in items]
    return render(request, 'reports/forecast_dashboard.html', {'forecasts': forecasts})