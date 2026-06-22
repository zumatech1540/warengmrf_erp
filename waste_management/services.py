from decimal import Decimal
from inventory.models import Item, StockMovement
from core.models import Transaction, Department

def process_waste_intake(*, category, quantity, source, user, waste_obj):

    # -----------------------
    # INVENTORY UPDATE
    # -----------------------
    item, _ = Item.objects.get_or_create(
        name=category.name,
        defaults={"category": "other", "unit": "kg"}
    )

    StockMovement.objects.create(
        item=item,
        movement_type="in",
        quantity=quantity,
        reason=f"Waste Intake - {source}",
        created_by=user
    )

    # -----------------------
    # AUTO DEPARTMENT
    # -----------------------
    department, _ = Department.objects.get_or_create(name="waste")

    # -----------------------
    # FINANCE / TRANSACTIONS
    # -----------------------
    Transaction.objects.create(
        type="waste",
        department=department,
        description=f"{quantity}kg {category.name} from {source}",
        created_by=user
    )