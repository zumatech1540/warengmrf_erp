from datetime import datetime
from decimal import Decimal

# Django core
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.template.loader import get_template
from django.conf import settings
from django.contrib import messages

from core.models import Supplier

# PDF generator
from xhtml2pdf import pisa

# Core app
from core.models import Transaction, Department
from core.services import get_or_create_department
from core.utils import get_department

# Auth
from accounts.decorators import role_required

# Inventory models (NO Supplier here anymore)
from inventory.models import Item, StockMovement

# Waste models (ONLY waste objects here)
from .models import (
    WasteIntake,
    WasteCategory,
    WastePurchase,
    WasteStatusHistory,
)

from .utils import update_waste_status
from .services import process_waste_intake

@login_required
@role_required(["collection", "super_admin", "director"])
def waste_dashboard(request):
    ...

# -------------------------
# WASTE DASHBOARD (ONLY ONE)
# -------------------------
@login_required
@role_required(["collection", "super_admin", "director"])
def waste_dashboard(request):

    data = WasteIntake.objects.all()

    context = {
        "total": data.count(),
        "received": data.filter(status="received").count(),
        "processing": data.filter(status="processing").count(),
        "completed": data.filter(status="completed").count(),
        "total_quantity": data.aggregate(total=Sum("quantity"))["total"] or 0,
        "recent_waste": data.select_related("category").order_by("-created_at")[:10],
        "category_stats": data.values("category__name")
                              .annotate(total=Count("id"))
                              .order_by("-total"),
    }

    return render(request, "waste_management/dashboard.html", context)

def supplier_display(supplier):
    return getattr(supplier, "company_name", "Walk-in")

from decimal import Decimal


@login_required
def waste_intake(request):

    categories = WasteCategory.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == "POST":

        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        quantity = request.POST.get('quantity')

        # -------------------------
        # VALIDATION
        # -------------------------
        if not category_id or not quantity:
            return HttpResponse("Category and quantity required", status=400)

        try:
            quantity = Decimal(quantity)
        except:
            return HttpResponse("Invalid quantity", status=400)

        # -------------------------
        # GET OBJECTS SAFELY
        # -------------------------
        try:
            category = WasteCategory.objects.get(id=category_id)
        except WasteCategory.DoesNotExist:
            return HttpResponse("Invalid category", status=400)

        supplier = None
        if supplier_id:
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                return HttpResponse("Invalid supplier selected", status=400)

        # -------------------------
        # CREATE WASTE INTAKE
        # -------------------------
        waste = WasteIntake.objects.create(
            category=category,
            supplier=supplier,
            quantity=quantity,
            created_by=request.user,
            status='received'
        )

        # -------------------------
        # INVENTORY SYNC
        # -------------------------
        item, _ = Item.objects.get_or_create(
            name=category.name,
            defaults={"category": "other", "unit": "kg"}
        )

        StockMovement.objects.create(
            item=item,
            movement_type="in",
            quantity=quantity,
            reason=f"Waste Intake - {supplier.company_name} ({supplier.phone})" if supplier else "Waste Intake - Walk-in",
            created_by=request.user
        )

        # -------------------------
        # TRANSACTION LOG
        # -------------------------
        Transaction.objects.create(
            type="waste_intake",
            department = get_or_create_department("waste"),
            description=f"{quantity}kg {category.name} from {getattr(supplier, 'company_name', 'Walk-in')}",
            created_by=request.user
        )

        return redirect("waste_dashboard")

    return render(request, "waste_management/intake.html", {
        "categories": categories,
        "suppliers": suppliers
    })
# -------------------------
# WASTE LIST
# -------------------------



@login_required
def waste_list(request):

    wastes = WasteIntake.objects.select_related(
        'category',
        'supplier',
        'created_by'
    ).all().order_by('-created_at')

    categories = WasteCategory.objects.order_by('name')

    search = request.GET.get('search')
    status = request.GET.get('status')
    category = request.GET.get('category')

    if search:
        wastes = wastes.filter(
            Q(supplier__name__icontains=search) |
            Q(category__name__icontains=search)
        )

    if status and status != "all":
        wastes = wastes.filter(status=status)

    if category and category != "all":
        wastes = wastes.filter(category_id=category)

    return render(request, 'waste_management/waste_list.html', {
        'wastes': wastes,
        'categories': categories,
        'search': search,
        'selected_status': status,
        'selected_category': category,
    })

@login_required
def waste_status_history(request, waste_id):

    history = WasteStatusHistory.objects.filter(
        waste_id=waste_id
    ).order_by('-changed_at')

    return render(request, 'waste_management/status_history.html', {
        'history': history
    })







@login_required
def change_waste_status(request, waste_id, status):

    # =========================
    # ROLE SECURITY (IMPORTANT)
    # =========================
    if request.user.role not in ['supervisor', 'manager']:
        return HttpResponse("❌ You are not allowed to change waste status", status=403)

    waste_obj = get_object_or_404(WasteIntake, id=waste_id)

    valid_statuses = ['received', 'processing', 'completed']

    # =========================
    # VALIDATION
    # =========================
    if status not in valid_statuses:
        return HttpResponse("Invalid status", status=400)

    # =========================
    # PREVENT NO-CHANGE UPDATES
    # =========================
    if waste_obj.status == status:
        return redirect('waste_list')

    # =========================
    # ERP AUDIT UPDATE
    # =========================
    update_waste_status(
        waste=waste_obj,
        new_status=status,
        user=request.user,
        comment=f"{waste_obj.status} → {status}"
    )

    return redirect('waste_list')



@login_required
def update_status_ajax(request):

    if request.method == "POST":

        if request.user.role not in ['supervisor', 'manager']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        waste_id = request.POST.get('id')
        new_status = request.POST.get('status')

        waste = WasteIntake.objects.get(id=waste_id)

        update_waste_status(
            waste=waste,
            new_status=new_status,
            user=request.user,
            comment="Inline status update"
        )

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)



@login_required
def waste_analytics(request):

    data = WasteIntake.objects.values('status').annotate(total=Count('id'))

    chart_data = {
        "received": 0,
        "processing": 0,
        "completed": 0
    }

    for d in data:
        chart_data[d['status']] = d['total']

    return render(request, 'waste_management/analytics.html', {
        'chart': chart_data
    })

@login_required
def waste_monthly_report(request):

    wastes = WasteIntake.objects.all().order_by('-created_at')

    template = get_template('waste_management/monthly_report.html')

    html = template.render({
        'wastes': wastes,
        'date': datetime.now()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="waste_report.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response



@login_required
def collector_dashboard(request):
    user = request.user
    today = timezone.now().date()

    # ==========================================
    # INTERNAL WASTE INTAKE (USER ONLY)
    # ==========================================
    my_waste = WasteIntake.objects.filter(created_by=user)

    total_waste = my_waste.aggregate(total=Sum('quantity'))['total'] or 0
    received = my_waste.filter(status='received').count()
    processing = my_waste.filter(status='processing').count()
    completed = my_waste.filter(status='completed').count()

    # ==========================================
    # RECENT LOGS (USER ONLY - MAX 10 RECORDS)
    # ==========================================
    recent_purchases = WastePurchase.objects.select_related('supplier', 'category')\
        .filter(created_by=user)\
        .order_by('-created_at')[:10]

    latest_purchase = recent_purchases[0] if recent_purchases else None

    total_purchases = WastePurchase.objects.filter(created_by=user).count()

    total_paid = WastePurchase.objects.filter(created_by=user).aggregate(
        total=Sum('total_amount')
    )['total'] or 0

    # ==========================================
    # TODAY'S SHIFT LOGS
    # ==========================================
    todays_purchases = WastePurchase.objects.filter(
        created_by=user,
        created_at__date=today
    )

    today_qty = todays_purchases.aggregate(total=Sum('quantity'))['total'] or 0

    today_cash_payout = todays_purchases.filter(is_paid_on_delivery=True)\
        .aggregate(total=Sum('total_amount'))['total'] or 0

    today_credit_debt = todays_purchases.filter(is_paid_on_delivery=False)\
        .aggregate(total=Sum('total_amount'))['total'] or 0

    # ==========================================
    # GLOBAL ACCESS DATA (FIXED)
    # ==========================================
    suppliers = Supplier.objects.filter(status='active').count()

    categories = WastePurchase.objects.values('category__name')\
    .annotate(total_qty=Sum('quantity'))\
    .order_by('-total_qty')
    # ==========================================
    # RENDER
    # ==========================================
    return render(request, 'waste_management/collector_dashboard.html', {
        'total_waste': total_waste,
        'received': received,
        'processing': processing,
        'completed': completed,

        'recent_purchases': recent_purchases,
        'total_purchases': total_purchases,
        'latest_purchase': latest_purchase,
        'total_paid': total_paid,
        'suppliers': suppliers,
        'categories': categories,

        'today_qty': today_qty,
        'today_cash_payout': today_cash_payout,
        'today_credit_debt': today_credit_debt,
        'cv_date': today,
    })

@login_required
def waste_purchase(request):

    suppliers = Supplier.objects.all()
    categories = WasteCategory.objects.all()

    print("🔥 SUPPLIERS IN WASTE:", suppliers.count())

    if request.method == "POST":

        supplier_id = request.POST.get('supplier')
        category_id = request.POST.get('category')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')

        WastePurchase.objects.create(
            supplier_id=supplier_id,
            category_id=category_id,
            quantity=quantity,
            unit_price=unit_price,
            created_by=request.user
        )

        return redirect('waste_dashboard')

    return render(request, 'waste_management/add_purchase.html', {
        'suppliers': suppliers,
        'categories': categories
    })
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from waste_management.models import WastePurchase

@login_required
def purchase_detail(request, purchase_id):

    purchase = get_object_or_404(
        WastePurchase.objects.select_related('supplier', 'category', 'created_by'),
        id=purchase_id
    )

    return render(request, 'waste_management/purchase_detail.html', {
        'purchase': purchase
    })






@login_required
def add_supplier(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if not name:
            messages.error(request, "Supplier name is required.")
            return redirect("add_supplier")

        if not phone:
            messages.error(request, "Phone number is required.")
            return redirect("add_supplier")

        # Duplicate phone check
        if Supplier.objects.filter(phone=phone).exists():
            messages.error(
                request,
                f"Supplier with phone {phone} already exists."
            )
            return redirect("add_supplier")

        Supplier.objects.create(
            company_name=name,
            contact_person=request.POST.get("contact_person", ""),
            phone=phone,
            email=request.POST.get("email", ""),
            address=request.POST.get("address", ""),
        )

        messages.success(request, "Supplier added successfully.")
        return redirect("supplier_list")

    return render(request, "inventory/add_supplier.html")

@login_required
def add_item(request):

    suppliers = Supplier.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        unit = request.POST.get('unit')
        supplier_id = request.POST.get('supplier')

        item = Item.objects.create(
            name=name,
            description=description,
            unit=unit
        )

        # OPTIONAL: link supplier if your model supports it
        # item.supplier_id = supplier_id
        # item.save()

        return redirect('inventory_home')

    return render(request, 'inventory/intake.html', {
        'suppliers': suppliers
    })




@login_required
def download_receipt(request, purchase_id):
    # Fetch the purchase with all related data optimized
    purchase = get_object_or_404(
        WastePurchase.objects.select_related('supplier', 'category', 'created_by'),
        id=purchase_id
    )
    
    # Load the receipt template
    template = get_template('waste_management/receipt_pdf.html')
    
    context = {
        'purchase': purchase,
        'company_name': "Warengmrf",  # Your company branding
        'generated_at': purchase.created_at
    }
    
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    
    # 'attachment' forces a download. Change to 'inline' if you want it to open in the browser tab instead
    response['Content-Disposition'] = f'attachment; filename="Receipt_WP_{purchase.id}.pdf"'
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('❌ Error generating receipt PDF', status=500)
        
    return response