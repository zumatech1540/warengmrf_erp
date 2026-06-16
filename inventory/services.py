from django.utils import timezone
from .models import Item
from .models import PurchaseOrder, PurchaseOrderItem
from inventory.utils import generate_po_number  # if you have it
from inventory.models import Supplier


def generate_auto_purchase_orders(user=None):

    low_stock_items = Item.objects.filter(
        current_stock__lte=models.F('reorder_level')
    )

    created_pos = []

    # Group by supplier (if you don't have item-supplier mapping yet,
    # we assign first active supplier)
    supplier = Supplier.objects.filter(status='active').first()

    if not supplier:
        return []

    # Create ONE PO per run (can be improved later to group by supplier)
    po = PurchaseOrder.objects.create(
        po_number=generate_po_number(),
        supplier=supplier,
        status='draft',
        created_by=user,
        created_at=timezone.now()
    )

    total_amount = 0

    for item in low_stock_items:

        qty = item.reorder_quantity
        price = item.unit_price

        line_total = qty * price
        total_amount += line_total

        PurchaseOrderItem.objects.create(
            purchase_order=po,
            item=item,
            quantity=qty,
            unit_price=price,
            total=line_total
        )

    po.total_amount = total_amount
    po.save()

    return po