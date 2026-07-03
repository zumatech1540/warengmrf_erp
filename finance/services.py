from decimal import Decimal

from .models import (
    JournalEntry,
    JournalLine,
    ChartOfAccount
)


def create_journal(
    reference,
    description,
    debit_account,
    credit_account,
    amount,
    user=None
):

    amount = Decimal(str(amount))

    try:
        debit = ChartOfAccount.objects.get(name=debit_account)
    except ChartOfAccount.DoesNotExist:
        raise Exception(
            f"Debit account '{debit_account}' does not exist."
        )

    try:
        credit = ChartOfAccount.objects.get(name=credit_account)
    except ChartOfAccount.DoesNotExist:
        raise Exception(
            f"Credit account '{credit_account}' does not exist."
        )

    journal = JournalEntry.objects.create(
        reference=reference,
        description=description,
        created_by=user
    )

    JournalLine.objects.create(
        journal=journal,
        account=debit,
        entry_type='debit',
        amount=amount
    )

    JournalLine.objects.create(
        journal=journal,
        account=credit,
        entry_type='credit',
        amount=amount
    )

    return journal