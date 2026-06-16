from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse

from datetime import datetime
from django.db import transaction

from .models import Payment, InvoiceSequence


# =========================
# PAYMENT RECEIPT PDF
# =========================
def generate_payment_receipt(payment):

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # HEADER
    p.setFont("Helvetica-Bold", 16)
    p.drawString(180, 800, "NAIBERI MRF ERP")

    p.setFont("Helvetica", 12)
    p.drawString(200, 770, "PAYMENT RECEIPT")

    p.line(50, 760, 550, 760)

    # DETAILS
    p.drawString(60, 720, f"Payment ID: {payment.id}")
    p.drawString(60, 700, f"Amount: KES {payment.amount}")
    p.drawString(60, 680, f"Method: {payment.method}")
    p.drawString(60, 660, f"Reference: {payment.reference}")
    p.drawString(60, 640, f"Date: {payment.created_at}")

    # CUSTOMER / SUPPLIER
    if payment.payment_type == "ar":
        p.drawString(60, 610, f"Customer: {payment.ar.customer_name}")
        p.drawString(60, 590, "Type: Accounts Receivable Payment")

    elif payment.payment_type == "ap":
        p.drawString(60, 610, f"Supplier: {payment.ap.supplier_name}")
        p.drawString(60, 590, "Type: Accounts Payable Payment")

    p.line(50, 560, 550, 560)

    p.drawString(60, 520, "Thank you for using Naiberi MRF ERP System")

    p.showPage()
    p.save()

    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf')


# =========================
# SAFE RECEIPT NUMBER GENERATOR
# =========================
def generate_receipt_number():

    year = datetime.now().year

    with transaction.atomic():

        last_payment = Payment.objects.select_for_update().order_by('-id').first()

        if not last_payment or not last_payment.receipt_number:
            new_number = 1
        else:
            try:
                new_number = int(last_payment.receipt_number.split('-')[1]) + 1
            except:
                new_number = last_payment.id + 1

        return f"RCP-{str(new_number).zfill(6)}-{year}"


# =========================
# INVOICE NUMBER GENERATOR (ERP SAFE)
# =========================
def generate_invoice_number():

    year = datetime.now().year

    with transaction.atomic():

        seq, created = InvoiceSequence.objects.select_for_update().get_or_create(
            year=year,
            defaults={"last_number": 0}
        )

        seq.last_number += 1
        seq.save()

        return f"INV-{year}-{str(seq.last_number).zfill(6)}"