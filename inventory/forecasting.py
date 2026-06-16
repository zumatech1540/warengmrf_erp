from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from .models import StockMovement, Item


def forecast_item_demand(item, days=30):

    # =========================
    # TIME WINDOW
    # =========================
    start_date = timezone.now() - timedelta(days=days)

    # =========================
    # TOTAL STOCK OUT (CONSUMPTION)
    # =========================
    total_out = StockMovement.objects.filter(
        item=item,
        movement_type='out',
        created_at__gte=start_date
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # =========================
    # DAILY AVERAGE USAGE
    # =========================
    daily_usage = total_out / days if days > 0 else 0

    # =========================
    # STOCK REMAINING DAYS
    # =========================
    if daily_usage > 0:
        days_remaining = item.current_stock / daily_usage
    else:
        days_remaining = 999  # no usage

    # =========================
    # RECOMMENDED ORDER DATE
    # =========================
    reorder_point_days = item.reorder_level / daily_usage if daily_usage > 0 else None

    return {
        "item": item.name,
        "current_stock": item.current_stock,
        "daily_usage": round(daily_usage, 2),
        "days_remaining": round(days_remaining, 1),
        "reorder_level": item.reorder_level,
        "recommended_reorder": reorder_point_days
    }