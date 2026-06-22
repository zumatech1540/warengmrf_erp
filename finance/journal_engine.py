from decimal import Decimal
from django.db import transaction
from .models import JournalEntry, JournalLine
from core.models import ChartOfAccount


def get_account(name):
    return ChartOfAccount.objects.get(name=name)


def create_journal(reference, description, lines, user=None):
    """
    lines format:
    [
        {"account": "Cash", "type": "debit", "amount": 1000},
        {"account": "Revenue", "type": "credit", "amount": 1000},
    ]
    """

    with transaction.atomic():

        journal = JournalEntry.objects.create(
            reference=reference,
            description=description,
            created_by=user
        )

        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for line in lines:

            amount = Decimal(str(line["amount"]))

            account = get_account(line["account"])

            JournalLine.objects.create(
                journal=journal,
                account=account,
                entry_type=line["type"],
                amount=amount
            )

            if line["type"] == "debit":
                total_debit += amount
            else:
                total_credit += amount

        # SAFETY CHECK (VERY IMPORTANT)
        if total_debit != total_credit:
            raise ValueError(
                f"Journal not balanced: Dr {total_debit} != Cr {total_credit}"
            )

        return journal