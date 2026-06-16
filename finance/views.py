from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .invoice_pdf import generate_invoice_pdf
from decimal import Decimal

from .models import (
    Income,
    Expense,
    Payment,
    AccountReceivable,
    AccountPayable,
    GeneralLedger
)

from .utils import generate_receipt_number, generate_payment_receipt
from core.utils import log_action


# =========================
# DASHBOARD
# =========================
@login_required
def finance_dashboard(request):

    total_income = Income.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    profit = total_income - total_expense

    return render(request, 'finance/dashboard.html', {
        'total_income': total_income,
        'total_expense': total_expense,
        'profit': profit
    })


# =========================
# INCOME
# =========================
@login_required
def income_list(request):
    incomes = Income.objects.all().order_by('-date')
    return render(request, 'finance/income_list.html', {'incomes': incomes})


@login_required
def add_income(request):
    if request.method == "POST":
        Income.objects.create(
            source=request.POST['source'],
            amount=request.POST['amount'],
            description=request.POST['description']
        )
        return redirect('income_list')

    return render(request, 'finance/add_income.html')


# =========================
# EXPENSE
# =========================
@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'finance/expense_list.html', {'expenses': expenses})


@login_required
def add_expense(request):
    if request.method == "POST":
        Expense.objects.create(
            category=request.POST['category'],
            amount=request.POST['amount'],
            description=request.POST['description']
        )
        return redirect('expense_list')

    return render(request, 'finance/add_expense.html')


# =========================
# AR LIST
# =========================
@login_required
def ar_list(request):
    receivables = AccountReceivable.objects.all().order_by('-id')
    return render(request, 'finance/ar_list.html', {'receivables': receivables})


# =========================
# AP LIST
# =========================
@login_required
def ap_list(request):
    payables = AccountPayable.objects.all().order_by('-id')
    return render(request, 'finance/ap_list.html', {'payables': payables})


# =========================
# ADD AR
# =========================
@login_required
def add_ar(request):
    if request.method == "POST":

        AccountReceivable.objects.create(
            customer_name=request.POST['customer_name'],
            amount_due=request.POST['amount_due'],
            amount_paid=request.POST.get('amount_paid', 0),
            description=request.POST.get('description', '')
        )

        return redirect('ar_list')

    return render(request, 'finance/add_ar.html')


# =========================
# ADD AP
# =========================
@login_required
def add_ap(request):
    if request.method == "POST":

        AccountPayable.objects.create(
            supplier_name=request.POST['supplier_name'],
            amount_due=request.POST['amount_due'],
            amount_paid=request.POST.get('amount_paid', 0),
            description=request.POST.get('description', '')
        )

        return redirect('ap_list')

    return render(request, 'finance/add_ap.html')


# =========================
# MAKE PAYMENT (CLEAN ERP CORE)
# =========================
@login_required
def make_payment(request):

    if request.method == "POST":

        with transaction.atomic():

            payment_type = request.POST['payment_type']
            amount = Decimal(request.POST['amount'])
            method = request.POST['method']
            reference = request.POST.get('reference', '')

            if amount <= 0:
                raise ValueError("Amount must be greater than zero")

            # =========================
            # AR PAYMENT
            # =========================
            if payment_type == "ar":

                ar = AccountReceivable.objects.select_for_update().get(
                    id=request.POST['ar_id']
                )

                if amount > (ar.amount_due - ar.amount_paid):
                    raise ValueError("Payment exceeds outstanding balance")

                ar.amount_paid += amount
                ar.save()

                payment = Payment.objects.create(
                    payment_type='ar',
                    ar=ar,
                    amount=amount,
                    method=method,
                    reference=reference,
                    receipt_number=generate_receipt_number()
                )

                GeneralLedger.objects.create(
                    account_name="Accounts Receivable",
                    entry_type="credit",
                    amount=amount,
                    description=f"Payment received from {ar.customer_name}"
                )

                GeneralLedger.objects.create(
                    account_name="Cash / Bank",
                    entry_type="debit",
                    amount=amount,
                    description=f"Cash received from {ar.customer_name}"
                )

                log_action(
                    user=request.user,
                    action_type="payment",
                    model_name="AccountReceivable",
                    record_id=ar.id,
                    description=f"AR payment received from {ar.customer_name} amount {amount}"
                )


            # =========================
            # AP PAYMENT
            # =========================
            elif payment_type == "ap":

                ap = AccountPayable.objects.select_for_update().get(
                    id=request.POST['ap_id']
                )

                if amount > (ap.amount_due - ap.amount_paid):
                    raise ValueError("Payment exceeds outstanding balance")

                ap.amount_paid += amount
                ap.save()

                payment = Payment.objects.create(
                    payment_type='ap',
                    ap=ap,
                    amount=amount,
                    method=method,
                    reference=reference,
                    receipt_number=generate_receipt_number()
                )

                GeneralLedger.objects.create(
                    account_name="Accounts Payable",
                    entry_type="debit",
                    amount=amount,
                    description=f"Payment made to {ap.supplier_name}"
                )

                GeneralLedger.objects.create(
                    account_name="Cash / Bank",
                    entry_type="credit",
                    amount=amount,
                    description=f"Cash paid to {ap.supplier_name}"
                )

                log_action(
                    user=request.user,
                    action_type="payment",
                    model_name="AccountPayable",
                    record_id=ap.id,
                    description=f"AP payment made to {ap.supplier_name} amount {amount}"
                )

        return redirect('payment_receipt', payment_id=payment.id)

    return render(request, 'finance/make_payment.html', {
        'ars': AccountReceivable.objects.all().order_by('-id'),
        'aps': AccountPayable.objects.all().order_by('-id'),
    })


# =========================
# RECEIPT
# =========================
@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return generate_payment_receipt(payment)

def invoice_pdf_view(request, ar_id):
    invoice = AccountReceivable.objects.get(id=ar_id)
    return generate_invoice_pdf(invoice)