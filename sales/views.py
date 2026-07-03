from decimal import Decimal
from core.models import AuditLog
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa


from .models import Sale, Customer
from inventory.models import Item

from core.models import Transaction, Department

from finance.models import (
AccountReceivable,
JournalEntry,
JournalLine,
ChartOfAccount
)

from finance.utils import generate_invoice_number

# =====================================================

# SALES DASHBOARD

# =====================================================

@login_required
def sales_dashboard(request):

    sales = Sale.objects.all().order_by('-created_at')

    total_sales = sales.count()

    total_revenue = sum(
        sale.total_amount for sale in sales
    )

    pending_sales = Sale.objects.filter(
        status='pending'
    ).count()

    total_customers = Customer.objects.count()

    context = {
        'sales': sales,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'pending_sales': pending_sales,
        'total_customers': total_customers,
    }

    return render(
        request,
        'sales/dashboard.html',
        context
    )

# =====================================================

# ADD CUSTOMER

# =====================================================

@login_required
def add_customer(request):
    if request.method == "POST":
        Customer.objects.create(
            company_name=request.POST.get('company_name'),
            contact_person=request.POST.get('contact_person', ''),
            phone=request.POST.get('phone'),
            email=request.POST.get('email', ''),
            address=request.POST.get('address', '')
        )
        return redirect('create_sale')
    
    # This renders the page when the user visits via GET
    return render(request, 'sales/add_customer.html')
# =====================================================

# CREATE SALE

# =====================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import logging

from .models import Sale, Customer
from inventory.models import Item
from finance.models import (
    JournalEntry,
    JournalLine,
    ChartOfAccount,
    AccountReceivable
)
from core.models import Transaction, Department

logger = logging.getLogger(__name__)


@login_required
def create_sale(request):

    context = {
        'customers': Customer.objects.all().order_by('company_name'),
        'items': Item.objects.filter(
            current_stock__gt=0
        ).order_by('name'),
        'error': None
    }

    if request.method == "POST":

        try:

            with transaction.atomic():

                customer_id = request.POST.get('customer')
                item_id = request.POST.get('item')

                status = request.POST.get(
                    'status',
                    'pending'
                )

                # =========================
                # TIMBER FIELDS
                # =========================

                timber_size = request.POST.get(
                    'timber_size',
                    ''
                )

                timber_length = request.POST.get(
                    'timber_length',
                    ''
                )

                timber_pieces = request.POST.get(
                    'timber_pieces',
                    ''
                )

                quantity_value = request.POST.get(
                    'quantity',
                    ''
                )

                unit_price_value = request.POST.get(
                    'unit_price',
                    '0'
                )

                # =========================
                # PRICE
                # =========================

                price = Decimal(
                    unit_price_value or "0"
                )

                # =========================
                # TIMBER SALES
                # =========================

                if timber_pieces:

                    qty = Decimal(timber_pieces)

                    sale = Sale.objects.create(
                        customer_id=customer_id,
                        item_id=item_id,
                        quantity=qty,
                        timber_size=timber_size,
                        timber_length=timber_length,
                        timber_pieces=int(timber_pieces),
                        unit_price=price,
                        status=status,
                        created_by=request.user
                    )
                    log_action(
                        user=request.user,
                        action_type="create",
                        model_name="Sale",
                        record_id=sale.id,
                        description=f"Created Sale #{sale.id}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                        user_agent=request.META.get("HTTP_USER_AGENT", "")
                    )
                # =========================
                # NORMAL SALES
                # =========================

                else:

                    if not quantity_value:

                        raise ValueError(
                            "Quantity is required."
                        )

                    qty = Decimal(quantity_value)

                    sale = Sale.objects.create(
                        customer_id=customer_id,
                        item_id=item_id,
                        quantity=qty,
                        unit_price=price,
                        status=status,
                        created_by=request.user
                    )

                # =========================
                # ACCOUNTING
                # =========================

                debit_code = (
                    '1001'
                    if status == 'paid'
                    else '1101'
                )

                debit_account = ChartOfAccount.objects.get(
                    code=debit_code
                )

                credit_account = ChartOfAccount.objects.get(
                    code='4001'
                )

                journal = JournalEntry.objects.create(
                    reference=f"INV-{sale.id}",
                    description=(
                        f"Sale #{sale.id} - "
                        f"{sale.customer.company_name}"
                    ),
                    created_by=request.user,
                    date=timezone.now()
                )

                JournalLine.objects.create(
                    journal=journal,
                    account=debit_account,
                    entry_type='debit',
                    amount=sale.total_amount
                )

                JournalLine.objects.create(
                    journal=journal,
                    account=credit_account,
                    entry_type='credit',
                    amount=sale.total_amount
                )

                # =========================
                # TRANSACTION LOG
                # =========================

                finance_dept = Department.objects.filter(
                    name__icontains='Finance'
                ).first()

                if finance_dept:

                    Transaction.objects.create(
                        type='finance',
                        department=finance_dept,
                        description=f"Sale #{sale.id}",
                        amount=sale.total_amount,
                        created_by=request.user
                    )

                # =========================
                # ACCOUNTS RECEIVABLE
                # =========================

                if status == 'pending':

                    AccountReceivable.objects.create(
                        customer_name=sale.customer.company_name,
                        amount_due=sale.total_amount,
                        amount_paid=0,
                        description=f"Sale #{sale.id}",
                        due_date=timezone.now().date()
                    )

                return redirect('sales_dashboard')

        except Exception as e:

            logger.error(
                f"Sale creation failed: {e}",
                exc_info=True
            )

            context['error'] = (
                f"Transaction failed: {str(e)}"
            )

    return render(
        request,
        'sales/create_sale.html',
        context
    )

# =====================================================

# SALES LIST

# =====================================================

@login_required
def sale_list(request):
    # Everything inside the function must be indented by 4 spaces
    sales = Sale.objects.all().order_by('-created_at')

    total_revenue = sum(
        sale.total_amount for sale in sales
    )

    total_customers = Customer.objects.count()

    return render(
        request,
        'sales/sale_list.html',
        {
            'sales': sales,
            'total_revenue': total_revenue,
            'total_customers': total_customers,
        }
    )

# =====================================================

# SALE INVOICE

# =====================================================

@login_required
def sale_invoice(request, sale_id):
    # Everything below is now correctly indented by 4 spaces
    sale = get_object_or_404(
        Sale,
        id=sale_id
    )

    return render(
        request,
        'sales/invoice.html',
        {
            'sale': sale
        }
    )

@login_required
def sale_invoice_pdf(request, sale_id):

    sale = get_object_or_404(
        Sale,
        id=sale_id
    )

    template = get_template(
        'sales/invoice.html'
    )

    html = template.render({
        'sale': sale
    })

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = (
        f'filename="invoice_{sale.id}.pdf"'
    )

    pisa.CreatePDF(
        html,
        dest=response
    )

    return response

from finance.models import Invoice

@login_required
def invoice_list(request):

    invoices = Invoice.objects.select_related(
        'sale'
    ).order_by('-created_at')

    return render(
        request,
        'finance/invoice_list.html',
        {
            'invoices': invoices
        }
    )

@login_required
def invoice_pdf_view(request, invoice_id):

    invoice = get_object_or_404(
        Invoice,
        id=invoice_id
    )

    return generate_invoice_pdf(invoice)