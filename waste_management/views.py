from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import WasteIntake, WasteCategory
from django.db.models import Q
from .models import WasteStatusHistory
from .utils import update_waste_status
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.db.models import Count
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime
from django.db.models import Sum, Count
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import WasteIntake, WasteCategory
from inventory.models import Item, StockMovement
from core.models import Transaction
from core.utils import get_department







# -------------------------
# WASTE DASHBOARD (ONLY ONE)
# -------------------------
@login_required
def waste_dashboard(request):

    total = WasteIntake.objects.count()

    received = WasteIntake.objects.filter(
        status='received'
    ).count()

    processing = WasteIntake.objects.filter(
        status='processing'
    ).count()

    completed = WasteIntake.objects.filter(
        status='completed'
    ).count()

    total_quantity = WasteIntake.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    recent_waste = WasteIntake.objects.select_related(
        'category'
    ).order_by('-created_at')[:10]

    category_stats = WasteIntake.objects.values(
        'category__name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'total': total,
        'received': received,
        'processing': processing,
        'completed': completed,
        'total_quantity': total_quantity,
        'recent_waste': recent_waste,
        'category_stats': category_stats,
    }

    return render(
        request,
        'waste_management/dashboard.html',
        context
    )


# -------------------------
# WASTE INTAKE FORM
# -------------------------



@login_required
def waste_intake(request):

    categories = WasteCategory.objects.all()

    if request.method == "POST":

        category_id = request.POST['category']
        quantity = float(request.POST['quantity'])
        source = request.POST['source']

        # 1. SAVE WASTE RECORD
        waste = WasteIntake.objects.create(
            category_id=category_id,
            quantity=quantity,
            source=source,
            created_by=request.user
        )

        # 2. GET CATEGORY NAME
        category_name = waste.category.name

        # 3. FIND OR CREATE INVENTORY ITEM
        item, created = Item.objects.get_or_create(
            name=category_name,
            defaults={
                "category": "other",
                "unit": "kg"
            }
        )

        # 4. UPDATE STOCK USING STOCKMOVEMENT (ERP CORRECT WAY)
        StockMovement.objects.create(
            item=item,
            movement_type='in',
            quantity=quantity,
            reason=f"Waste Intake from {source}",
            created_by=request.user
        )

        # 5. CREATE TRANSACTION LOG (CORE MODULE)
        Transaction.objects.create(
            type="waste",
            department=get_department("waste"),
            description=f"Received {quantity}kg {category_name} from {source}",
            created_by=request.user
        )

        return redirect('waste_dashboard')

    return render(request, 'waste_management/intake.html', {
        'categories': categories
    })

# -------------------------
# WASTE LIST
# -------------------------



@login_required
def waste_list(request):

    wastes = WasteIntake.objects.select_related('category', 'department') \
        .all().order_by('-created_at')

    categories = WasteCategory.objects.all()

    # =========================
    # FILTER VALUES
    # =========================
    search = request.GET.get('search')
    status = request.GET.get('status')
    category = request.GET.get('category')

    # =========================
    # SEARCH FILTER (source or category name)
    # =========================
    if search:
        wastes = wastes.filter(
            Q(source__icontains=search) |
            Q(category__name__icontains=search)
        )

    # =========================
    # STATUS FILTER
    # =========================
    if status and status != "all":
        wastes = wastes.filter(status=status)

    # =========================
    # CATEGORY FILTER
    # =========================
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