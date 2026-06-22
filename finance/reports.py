from decimal import Decimal
from django.db.models import Sum
from .models import JournalLine, JournalEntry

def trial_balance():
    """
    Returns all accounts with debit/credit totals
    """
    # ✅ FIX: Changed 'account_name' to 'account__name' to cross the relationship
    lines = JournalLine.objects.values(
        "account__name",
        "entry_type"
    ).annotate(total=Sum("amount"))

    report = {}

    for line in lines:
        acc = line["account__name"]  # ✅ Update reference here
        entry_type = line["entry_type"]
        total = line["total"] or Decimal("0")

        if not acc:
            acc = "Unassigned Account"

        if acc not in report:
            report[acc] = {"debit": Decimal("0"), "credit": Decimal("0")}

        report[acc][entry_type] = total

    return report


def income_statement():
    revenue = Decimal("0")
    expenses = Decimal("0")

    # ✅ FIX: Query lookups traverse through related account profile name
    income_lines = JournalLine.objects.filter(
        entry_type="credit",
        account__name__icontains="income"
    ).values_list("amount", flat=True)

    expense_lines = JournalLine.objects.filter(
        entry_type="debit",
        account__name__icontains="expense"
    ).values_list("amount", flat=True)

    revenue = sum(income_lines, Decimal("0"))
    expenses = sum(expense_lines, Decimal("0"))

    return {
        "revenue": revenue,
        "expenses": expenses,
        "profit": revenue - expenses
    }


def balance_sheet():
    assets = Decimal("0")
    liabilities = Decimal("0")
    equity = Decimal("0")

    # ✅ FIX: Updated all lookups to use 'account__name__icontains'
    asset_lines = JournalLine.objects.filter(
        account__name__icontains="cash"
    )

    liability_lines = JournalLine.objects.filter(
        account__name__icontains="payable"
    )

    equity_lines = JournalLine.objects.filter(
        account__name__icontains="capital"
    )

    for l in asset_lines:
        assets += l.amount

    for l in liability_lines:
        liabilities += l.amount

    for l in equity_lines:
        equity += l.amount

    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "check": assets == (liabilities + equity)
    }


def cash_flow():
    cash_in = Decimal("0")
    cash_out = Decimal("0")

    # ✅ FIX: Updated to 'account__name__icontains'
    cash_lines = JournalLine.objects.filter(
        account__name__icontains="cash"
    )

    for line in cash_lines:
        if line.entry_type == "debit":
            cash_in += line.amount
        else:
            cash_out += line.amount

    return {
        "cash_in": cash_in,
        "cash_out": cash_out,
        "net_cash": cash_in - cash_out
    }