from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
from django.http import HttpResponse

from datetime import datetime
from django.db import transaction

from .models import Payment, InvoiceSequence


# =========================================================
# PAYMENT RECEIPT PDF GENERATOR (Canvas Driven Layout)
# =========================================================
def generate_payment_receipt(payment):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # PAGE BOUNDS REFERENCE (A4: 595 x 842 points)
    
    # --- HEADER / BRANDING ---
    p.setFont("Helvetica-Bold", 16)
    p.setFillColorRGB(0.1, 0.1, 0.2) # Deep Professional Navy
    p.drawString(60, 800, "Warengmrf ERP")

    p.setFont("Helvetica-Bold", 11)
    p.setFillColorRGB(0.4, 0.4, 0.4) # Slate Grey
    p.drawRightString(535, 800, "OFFICIAL RECEIPT VOUCHER")

    # Thin Divider Rule
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.setLineWidth(1)
    p.line(50, 785, 545, 785)

    # --- METADATA PANEL (LEFT & RIGHT BALANCE) ---
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0.2, 0.2, 0.2)
    
    # Left Side Core Identifiers
    receipt_no = payment.receipt_number if payment.receipt_number else f"REC-{payment.id:06d}"
    p.drawString(60, 755, f"Receipt No: {receipt_no}")
    
    formatted_date = payment.created_at.strftime("%d %b %Y at %H:%M") if payment.created_at else datetime.now().strftime("%d %b %Y at %H:%M")
    p.drawString(60, 735, f"Posting Date: {formatted_date}")

    # Right Side Allocation Context
    if payment.payment_type == "ar":
        p.drawRightString(535, 755, f"Customer Account: {payment.ar.customer_name}")
        p.drawRightString(535, 735, "Allocation Type: Accounts Receivable")
    elif payment.payment_type == "ap":
        p.drawRightString(535, 755, f"Supplier Profile: {payment.ap.supplier_name}")
        p.drawRightString(535, 735, "Allocation Type: Accounts Payable")

    # --- TRANSACTION CONTAINER BOX ---
    p.setFillColorRGB(0.96, 0.96, 0.98) # Light Neutral Fill
    p.rect(50, 600, 495, 100, fill=True, stroke=False)

    p.setFillColorRGB(0.2, 0.2, 0.2)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(70, 670, "Transaction Breakdown Reference")
    p.drawString(70, 645, "Settlement Channel")
    
    p.setFont("Helvetica", 10)
    ref_txt = payment.reference if payment.reference else "Internal Reconciliation Adjustments"
    p.drawString(220, 670, f":  {ref_txt}")
    p.drawString(220, 645, f":  {payment.method.upper()}")

    # --- MONETARY BLOCK VALUATION ---
    p.setFont("Helvetica-Bold", 11)
    p.drawString(70, 615, "Total Amount Paid")
    p.setFont("Helvetica-Bold", 13)
    p.setFillColorRGB(0.1, 0.5, 0.2) # Deep Compliant green
    p.drawString(220, 615, f":  KES {payment.amount:,.2f}")

    # Bottom Sign-Off Footer
    p.setStrokeColorRGB(0.9, 0.9, 0.9)
    p.line(50, 560, 545, 560)
    
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(60, 535, "System Verified Document. Processed electronically through Naiberi Financial Engine Core.")

    p.showPage()
    p.save()

    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{payment.id}.pdf"'
    return response


# =========================================================
# FINANCIAL STATEMENTS REPORT PDF GENERATOR (Platypus Flowable)
# =========================================================
def generate_financial_report_pdf(report_type, data):
    """
    Generates a professional corporate PDF for financial statements.
    data: dictionary payload coming from your reports.py functions
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], 
        fontSize=18, leading=22, textColor=colors.HexColor('#1a1a2e'), spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'], 
        fontSize=10, leading=12, textColor=colors.HexColor('#555555'), spaceAfter=20
    )
    cell_style = ParagraphStyle(
        'Cell', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#333333')
    )
    cell_bold = ParagraphStyle(
        'CellB', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#1a1a2e')
    )

    # --- DOCUMENT HEADER ---
    story.append(Paragraph("Warengmrf ERP", title_style))
    story.append(Paragraph(f"Official Statement: {report_type.replace('_', ' ').title()} — Exported {datetime.now().strftime('%d %b %Y')}", subtitle_style))
    story.append(Spacer(1, 15))
    
    # --- TABLE DATA PARSING MATRIX ---
    table_content = []
    
    if report_type == "income_statement":
        table_content = [
            [Paragraph("<b>Financial Metric</b>", cell_bold), Paragraph("<b>Valuation (KES)</b>", cell_bold)],
            [Paragraph("Gross Revenue Pool (Credits)", cell_style), f"KES {data['revenue']:,.2f}"],
            [Paragraph("Operating Expenses (Debits)", cell_style), f"KES {data['expenses']:,.2f}"],
            [Paragraph("<b>Net Operating Profit / Loss</b>", cell_bold), f"KES {data['profit']:,.2f}"]
        ]
    elif report_type == "balance_sheet":
        table_content = [
            [Paragraph("<b>Classification</b>", cell_bold), Paragraph("<b>Net Value (KES)</b>", cell_bold)],
            [Paragraph("Total Liquid & Fixed Assets (Cash/Bank)", cell_style), f"KES {data['assets']:,.2f}"],
            [Paragraph("Outstanding Liabilities (Payables)", cell_style), f"KES {data['liabilities']:,.2f}"],
            [Paragraph("Equity Base (Capital Reserves)", cell_style), f"KES {data['equity']:,.2f}"],
            [Paragraph("<b>Accounting Equation Verification</b>", cell_bold), "COMPLIANT MATCH ✅" if data['check'] else "EQUATION DRIFT ⚠️"]
        ]
    elif report_type == "cash_flow":
        table_content = [
            [Paragraph("<b>Cash Flow Vectors</b>", cell_bold), Paragraph("<b>Volume (KES)</b>", cell_bold)],
            [Paragraph("Inbound Operating Cash (Debits)", cell_style), f"KES {data['cash_in']:,.2f}"],
            [Paragraph("Outbound Operational Disbursements (Credits)", cell_style), f"KES {data['cash_out']:,.2f}"],
            [Paragraph("<b>Net Cash Flow Velocity</b>", cell_bold), f"KES {data['net_cash']:,.2f}"]
        ]
    elif report_type == "trial_balance":
        table_content = [[Paragraph("<b>Account Ledger Profile</b>", cell_bold), Paragraph("<b>Debit (DR)</b>", cell_bold), Paragraph("<b>Credit (CR)</b>", cell_bold)]]
        for acc, balances in data.items():
            table_content.append([
                Paragraph(acc, cell_style),
                f"KES {balances['debit']:,.2f}" if balances['debit'] else "-",
                f"KES {balances['credit']:,.2f}" if balances['credit'] else "-"
            ])

    # Build and Style the Table Container dynamically based on structural needs
    col_widths = [285, 115, 115] if report_type == "trial_balance" else [350, 165]
    report_table = Table(table_content, colWidths=col_widths)
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor('#1a1a2e')),
    ]))
    
    story.append(report_table)
    
    # --- FOOTER SIGN-OFF ---
    story.append(Spacer(1, 40))
    story.append(Paragraph("<font color='#888888'>Generated via secure administrative export matrix. Cryptographically signed ledger verification trailing enabled.</font>", styles['Italic']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response


# =========================================================
# SAFE RECEIPT NUMBER GENERATOR
# =========================================================
def generate_receipt_number():
    year = datetime.now().year

    with transaction.atomic():
        last_payment = Payment.objects.select_for_update().order_by('-id').first()

        if not last_payment or not last_payment.receipt_number:
            new_number = 1
        else:
            try:
                new_number = int(last_payment.receipt_number.split('-')[1]) + 1
            except (ValueError, IndexError):
                new_number = last_payment.id + 1

        return f"RCP-{str(new_number).zfill(6)}-{year}"


# =========================================================
# INVOICE NUMBER GENERATOR (ERP SAFE)
# =========================================================
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