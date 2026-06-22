from .models import WasteStatusHistory


from django.db import transaction

def update_waste_status(waste, new_status, user, comment=None):

    old_status = waste.status
    waste.status = new_status
    waste.save()

    # STATUS HISTORY
    WasteStatusHistory.objects.create(
        waste=waste,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        comment=comment
    )

    # =========================
    # ONLY RUN ON FIRST COMPLETION
    # =========================
    if old_status != "completed" and new_status == "completed":

        from inventory.models import Item, StockMovement
        from django.db import transaction

        with transaction.atomic():

            item, created = Item.objects.get_or_create(
                name=waste.category.name,
                defaults={
                    "category": "other",
                    "unit": "kg",
                    "current_stock": 0
                }
            )

            # ADD STOCK
            item.current_stock += waste.quantity
            item.save()

            # OPTIONAL UPGRADE (THIS IS WHAT YOU ASKED)
            StockMovement.objects.create(
                item=item,
                movement_type="in",
                quantity=waste.quantity,
                reason=f"Waste Transfer (Waste ID: {waste.id})",
                created_by=user
            )
            
from inventory.models import Item


def transfer_to_inventory(waste):

    inventory_name = waste.category.name

    item, created = Item.objects.get_or_create(
        name=inventory_name,
        defaults={
            'category': waste.category.name.lower(),
            'unit': 'kg',
            'current_stock': 0
        }
    )

    item.current_stock += waste.quantity
    item.save()