from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .reports import income_statement, balance_sheet, cash_flow
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from .models import AccountPayable
from .utils import generate_receipt_number 
from .models import Department

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
from accounts.decorators import role_required


# =========================================================
# DASHBOARD (ACCRUAL-BASED REAL-TIME VALUATION)
# =========================================================
@login_required
@role_required(["finance", "super_admin", "director"])
def finance_dashboard(request):
    # Total Recognized Revenue (Direct Incomes + Outstanding Inbound Debts)
    direct_income = Income.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    unpaid_ar = AccountReceivable.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or Decimal('0')
    total_income = direct_income + unpaid_ar

    # Total Operational Outlays (Direct Expenditures + Accrued Vendor Commitments)
    direct_expense = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    accrued_ap = AccountPayable.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or Decimal('0')
    total_expense = direct_expense + accrued_ap

    # True Accrual Net Profit Margin
    profit = total_income - total_expense

    return render(request, 'finance/dashboard.html', {
        'total_income': total_income,
        'total_expense': total_expense,
        'profit': profit,
        'outstanding_liabilities': accrued_ap  # Extra context metric for the template
    })


# =========================================================
# INCOME / EXPENSE MANAGEMENT (VALUATION GUARDED)
# =========================================================
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Income, Department # Ensure both are imported here

@login_required
@role_required(["finance", "super_admin", "director"])
def add_income(request):
    # Fetch all departments for the dropdown
    departments = Department.objects.all()

    if request.method == "POST":
        try:
            # 1. Get data from POST
            source = request.POST.get('source')
            amount = request.POST.get('amount')
            description = request.POST.get('description', '')
            dept_id = request.POST.get('department')
            
            # 2. Validation
            if not dept_id:
                raise ValueError("A department must be selected.")
            
            # 3. Fetch the actual Department object
            dept_obj = Department.objects.get(id=dept_id)

            # 4. Create the record
            # We use 'department=dept_obj' to match the ForeignKey field
            Income.objects.create(
                source=source,
                amount=amount,
                description=description,
                department=dept_obj 
            )
            
            messages.success(request, "Revenue entry logged cleanly.")
            return redirect('income_list') 
            
        except Exception as e:
            messages.error(request, f"Submission failure: {str(e)}")

    # Return the page with the department list for the dropdown
    return render(request, 'finance/add_income.html', {'departments': departments})

@login_required
@role_required(["finance", "super_admin", "director"])
def add_expense(request):
    if request.method == "POST":
        try:
            amount_str = request.POST.get('amount', '0').strip()
            amount = Decimal(amount_str if amount_str else '0')
            if amount <= 0:
                raise ValueError("Operational expenditures must possess a positive base asset cost.")

            Expense.objects.create(
                category=request.POST['category'],
                amount=amount,
                description=request.POST.get('description', '')
            )
            messages.success(request, "Expense distribution record preserved.")
            return redirect('expense_list')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f"Submission failure: {str(e)}")

    return render(request, 'finance/add_expense.html')


# =========================================================
# ADD AR / DEBT TRACKING
# =========================================================
@login_required
@role_required(["finance", "super_admin", "director"])
def add_ar(request):
    if request.method == "POST":
        try:
            amount_due = Decimal(request.POST.get('amount_due', '0') or '0')
            amount_paid = Decimal(request.POST.get('amount_paid', '0') or '0')
            
            AccountReceivable.objects.create(
                customer_name=request.POST['customer_name'],
                amount_due=amount_due,
                amount_paid=amount_paid,
                description=request.POST.get('description', ''),
                due_date=request.POST['due_date']
            )
            messages.success(request, "Account Receivable ledger track established.")
            return redirect('ar_list')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f"Ledger validation fault: {str(e)}")

    return render(request, 'finance/add_ar.html')


# =========================================================
# ADD AP / LIABILITY RECORDING
# =========================================================



from waste_management.models import Supplier  

@login_required
@role_required(["finance", "super_admin", "director"])
def add_ap(request):
    if request.method == "POST":
        try:
            amount_due = Decimal(request.POST.get('amount_due', '0') or '0')
            amount_paid = Decimal(request.POST.get('amount_paid', '0') or '0')

            supplier_id = request.POST.get('supplier_id')
            if not supplier_id:
                raise ValueError("A valid supplier selection is required.")
                
            supplier_profile = get_object_or_404(Supplier, id=supplier_id)

            # Handles fields dynamically based on whether your model uses 'company_name' or 'name'
            resolved_name = getattr(supplier_profile, 'company_name', getattr(supplier_profile, 'name', 'Unknown Supplier'))

            AccountPayable.objects.create(
                supplier_name=resolved_name,
                amount_due=amount_due,
                amount_paid=amount_paid,
                description=request.POST.get('description', ''),
                due_date=request.POST['due_date']
            )
            messages.success(request, "Account Payable liability recognized successfully.")
            return redirect('ap_list')
        except (ValueError, InvalidOperation) as e:
            messages.error(request, f"Liability entry fault: {str(e)}")

    # Fetch all suppliers registered via the waste management platform
    suppliers = Supplier.objects.all().order_by('id')

    return render(request, 'finance/add_ap.html', {
        'suppliers': suppliers
    })

# =========================================================
# TRANSACTION ENGINE (ATOMIC CONCURRENCY PRESERVED)
# =========================================================
@login_required
@role_required(["finance", "super_admin", "director"])
def make_payment(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                payment_type = request.POST['payment_type']
                amount = Decimal(request.POST.get('amount', '0') or '0')
                method = request.POST.get('method', 'cash')
                reference = request.POST.get('reference', '')

                if amount <= 0:
                    raise ValueError("Allocation processing metrics must exceed KES 0.00")

                # -------------------------
                # AR CASH SETTLEMENT LOGIC
                # -------------------------
                if payment_type == "ar":
                    ar = AccountReceivable.objects.select_for_update().get(id=request.POST['ar_id'])
                    balance = ar.amount_due - ar.amount_paid
                    if amount > balance:
                        raise ValueError(f"Transaction excess error. Remaining debtor exposure is KES {balance}")

                    ar.amount_paid += amount
                    ar.save()

                    # ✅ FIXED: Now cleanly generates and assigns the receipt number on creation
                    payment = Payment.objects.create(
                        receipt_number=generate_receipt_number(),
                        payment_type='ar', 
                        ar=ar, 
                        amount=amount, 
                        method=method, 
                        reference=reference
                    )

                    GeneralLedger.objects.create(
                        account_name="Accounts Receivable", entry_type="credit", amount=amount,
                        description=f"Liquidation adjustment from customer: {ar.customer_name}"
                    )
                    GeneralLedger.objects.create(
                        account_name="Cash/Bank", entry_type="debit", amount=amount,
                        description=f"Capital injection collection via {method.upper()} from: {ar.customer_name}"
                    )

                    log_action(
                        user=request.user, action_type="payment", model_name="AccountReceivable",
                        record_id=ar.id, description=f"Processing inbound debtor liquid clear-down of KES {amount}"
                    )

                # -------------------------
                # AP DEBT CLEARANCE LOGIC
                # -------------------------
                elif payment_type == "ap":
                    ap = AccountPayable.objects.select_for_update().get(id=request.POST['ap_id'])
                    balance = ap.amount_due - ap.amount_paid
                    if amount > balance:
                        raise ValueError(f"Allocation balance error. Outstanding liability pool is KES {balance}")

                    ap.amount_paid += amount
                    ap.save()

                    # ✅ FIXED: Now cleanly generates and assigns the receipt number on creation
                    payment = Payment.objects.create(
                        receipt_number=generate_receipt_number(),
                        payment_type='ap', 
                        ap=ap, 
                        amount=amount, 
                        method=method, 
                        reference=reference
                    )

                    GeneralLedger.objects.create(
                        account_name="Accounts Payable", entry_type="debit", amount=amount,
                        description=f"Liability settlement reduction toward: {ap.supplier_name}"
                    )
                    GeneralLedger.objects.create(
                        account_name="Cash/Bank", entry_type="credit", amount=amount,
                        description=f"Outbound currency asset dispersion to vendor: {ap.supplier_name}"
                    )

                    log_action(
                        user=request.user, action_type="payment", model_name="AccountPayable",
                        record_id=ap.id, description=f"Executing account settlement of KES {amount} to vendor."
                    )

                messages.success(request, "Ledger system reconciliations confirmed.")
                return redirect('payment_receipt', payment_id=payment.id)

        except (ValueError, InvalidOperation) as e:
            messages.error(request, str(e))
            return redirect('make_payment')
        except Exception as e:
            messages.error(request, f"Fatal core banking execution failure: {str(e)}")
            return redirect('make_payment')

    
    all_ars = AccountReceivable.objects.all()
    all_aps = AccountPayable.objects.all()

    return render(request, 'finance/make_payment.html', {
        'ars': [ar for ar in all_ars if ar.amount_due > ar.amount_paid],
        'aps': [ap for ap in all_aps if ap.amount_due > ap.amount_paid],
    })

# =========================================================
# REPORT GENERATION & DATA ACCESS LOOKUPS
# =========================================================
@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return generate_payment_receipt(payment)

@login_required
def income_list(request):
    return render(request, 'finance/income_list.html', {
        'incomes': Income.objects.all().order_by('-date')
    })

@login_required
def expense_list(request):
    return render(request, 'finance/expense_list.html', {
        'expenses': Expense.objects.all().order_by('-date')
    })

@login_required
def ar_list(request):
    return render(request, 'finance/ar_list.html', {
        'receivables': AccountReceivable.objects.all().order_by('-id')
    })

@login_required
def ap_list(request):
    return render(request, 'finance/ap_list.html', {
        'payables': AccountPayable.objects.all().order_by('-id')
    })

@login_required
def invoice_pdf_view(request, ar_id):
    from .utils import generate_invoice_pdf
    invoice = get_object_or_404(AccountReceivable, id=ar_id)
    return generate_invoice_pdf(invoice)

@login_required
def ledger_list(request):
    return render(request, 'finance/ledger_list.html', {
        'entries': GeneralLedger.objects.all().order_by('-date')
    })

@login_required
@role_required(["finance", "super_admin", "director"])
def financial_reports(request):
    return render(request, "finance/reports.html", {
        "income": income_statement(),
        "balance_sheet": balance_sheet(),
        "cash_flow": cash_flow(),
    })
from .reports import income_statement, balance_sheet, cash_flow, trial_balance
from .utils import generate_financial_report_pdf

@login_required
@role_required(["finance", "super_admin", "director"])
def export_report_pdf(request, report_type):
    """
    Acts as a secure routing bridge that grabs fresh report calculations 
    and pipes them straight into the ReportLab PDF compiler.
    """
    if report_type == "income_statement":
        data = income_statement()
    elif report_type == "balance_sheet":
        data = balance_sheet()
    elif report_type == "cash_flow":
        data = cash_flow()
    elif report_type == "trial_balance":
        data = trial_balance()
    else:
        messages.error(request, "Invalid statement request index targeted.")
        return redirect('finance_dashboard') # Or whatever your core dashboard name is

    return generate_financial_report_pdf(report_type, data)