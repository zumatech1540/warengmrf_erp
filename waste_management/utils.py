from .models import WasteStatusHistory


def update_waste_status(waste, new_status, user, comment=""):

    old_status = waste.status

    if old_status == new_status:
        return waste

    waste.status = new_status
    waste.save()

    WasteStatusHistory.objects.create(
        waste=waste,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        comment=comment
    )

    return waste