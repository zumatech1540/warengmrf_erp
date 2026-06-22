from decimal import Decimal
from .models import JournalEntry, JournalLine
from django.utils import timezone


def create_journal(reference, description, debit_account, credit_account, amount, user=None):

    amount = Decimal(str(amount))

    journal = JournalEntry.objects.create(
        reference=reference,
        description=description,
        created_by=user,
        date=timezone.now()
    )

    JournalLine.objects.create(
        journal=journal,
        account_name=debit_account,
        entry_type='debit',
        amount=amount
    )

    JournalLine.objects.create(
        journal=journal,
        account_name=credit_account,
        entry_type='credit',
        amount=amount
    )

    return journal