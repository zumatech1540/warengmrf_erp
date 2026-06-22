from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Sale, Customer
from inventory.models import Item
from datetime import datetime
from django.db import transaction
from finance.models import JournalEntry, JournalLine, ChartOfAccount
from finance.utils import generate_invoice_number

# =========================
# SALES DASHBOARD
# =========================
@login_required
def sales_dashboard(request):
    sales = Sale.objects.all().order_by('-created_at')
    total_sales = sales.count()
    total_revenue = sum(sale.total_amount for sale in sales)

    return render(
        request,
        'sales/dashboard.html',
        {
            'sales': sales,
            'total_sales': total_sales,
            'total_revenue': total_revenue,
        }
    )

# =========================
# REGISTER CUSTOMER / BUYER
# =========================
@login_required
def add_customer(request):
    if request.method == "POST":
        Customer.objects.create(
            company_name=request.POST['company_name'],
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST['phone'],
            email=request.POST.get('email', ''),
            address=request.POST.get('address', '')
        )
        return redirect('create_sale') # Redirects back to the checkout/sale screen!

    return render(request, 'sales/add_customer.html')

# =========================
# CREATE SALE
# =========================


# =========================
# CREATE SALE WITH AUTO-LEDGER POSTING
# =========================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from datetime import datetime
from .models import Sale, Customer, Item
from finance.models import JournalEntry, JournalLine, ChartOfAccount
from finance.utils import generate_invoice_number

@login_required
def create_sale(request):
    customers = Customer.objects.all().order_by('company_name')
    items = Item.objects.filter(current_stock__gt=0).order_by('name')
    error = None

    if request.method == "POST":
        try:
            with transaction.atomic():
                quantity = Decimal(request.POST['quantity'])
                unit_price = Decimal(request.POST['unit_price'])
                total_amount = quantity * unit_price

                # 1. Create the Core Sale Record
                sale = Sale.objects.create(
                    customer_id=request.POST['customer'],
                    item_id=request.POST['item'],
                    quantity=quantity,
                    unit_price=unit_price,
                    created_by=request.user
                )

                # 2. Use the specific codes we established for perfect accuracy
                try:
                    cash_account = ChartOfAccount.objects.get(code="1001")
                    income_account = ChartOfAccount.objects.get(code="4001")
                except ChartOfAccount.DoesNotExist:
                    raise Exception("Mandatory Accounts (1001/4001) not found in Chart of Accounts.")

                # 3. Spin up the balanced structural Journal Entry Header
                # Note: Using 'reference' and 'date' as confirmed by your model
                entry = JournalEntry.objects.create(
                    reference=generate_invoice_number(),
                    description=f"Automated Sales Posting - Ref Sale #{sale.id} for {sale.customer.company_name}",
                    date=datetime.now() 
                )

                # 4. DEBIT ASSET: Post inbound money
                JournalLine.objects.create(
                    journal=entry,
                    account=cash_account,
                    entry_type="debit",
                    amount=total_amount
                )

                # 5. CREDIT REVENUE: Post earnings
                JournalLine.objects.create(
                    journal=entry,
                    account=income_account,
                    entry_type="credit",
                    amount=total_amount
                )

            return redirect('sales_dashboard')

        except Exception as e:
            error = str(e)

    return render(
        request,
        'sales/create_sale.html',
        {
            'customers': customers,
            'items': items,
            'error': error,
        }
    )

# =========================
# SALES LIST
# =========================
@login_required
def sale_list(request):
    sales = Sale.objects.all().order_by('-created_at')
    return render(request, 'sales/sale_list.html', {'sales': sales})

# =========================
# INVOICE VIEW
# =========================
@login_required
def sale_invoice(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'sales/invoice.html', {'sale': sale})

from django.db import transaction
from finance.models import JournalEntry, JournalLine
from finance.utils import generate_invoice_number # The ERP safe generator we confirmed!

def complete_sales_transaction(sale_data):
    with transaction.atomic():
        # 1. Process and save your sale record here...
        # sale = Sale.objects.create(...)
        
        # 2. Automatically spin up a balanced accounting Journal Entry
        entry = JournalEntry.objects.create(
            invoice_number=generate_invoice_number(),
            description=f"Sales Revenue - Invoice Ref #{sale_data['reference']}",
            created_at=datetime.now()
        )
        
        # 3. DEBIT: Increase your Liquid Assets (Cash/Bank Account)
        JournalLine.objects.create(
            journal=entry,
            account_id=cash_account_id, # Target your Chart of Accounts Cash Profile ID
            entry_type="debit",
            amount=sale_data['total_amount']
        )
        
        # 4. CREDIT: Recognize your Revenue (Income Account)
        JournalLine.objects.create(
            journal=entry,
            account_id=income_account_id, # Target your Chart of Accounts Income Profile ID
            entry_type="credit",
            amount=sale_data['total_amount']
        )