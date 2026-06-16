from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
import os


def generate_invoice_pdf(invoice):

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()

    # =========================
    # BRAND HEADER SECTION
    # =========================

    logo_path = "static/images/logo.png"

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=80, height=80)
        elements.append(logo)

    company_name = Paragraph(
        "<b>NAIBERI MRF ERP SYSTEM</b>",
        styles['Title']
    )

    elements.append(company_name)

    company_info = Paragraph(
        """
        Eldoret, Kenya<br/>
        Email: info@naiberi-erp.com<br/>
        Phone: +254 716 170 389
        """,
        styles['Normal']
    )

    elements.append(company_info)
    elements.append(Spacer(1, 12))

    # =========================
    # INVOICE HEADER BOX
    # =========================
    invoice_header = Paragraph(
        f"""
        <b>INVOICE</b><br/>
        Invoice No: {invoice.invoice_number}<br/>
        Date: {invoice.created_at if hasattr(invoice, 'created_at') else ''}
        """,
        styles['Normal']
    )

    elements.append(invoice_header)
    elements.append(Spacer(1, 12))

    # =========================
    # CUSTOMER INFO
    # =========================
    customer_info = Paragraph(
        f"""
        <b>Billed To:</b><br/>
        {invoice.customer.company_name}<br/>
        {invoice.customer.phone}<br/>
        {invoice.customer.email}
        """,
        styles['Normal']
    )

    elements.append(customer_info)
    elements.append(Spacer(1, 12))

    # =========================
    # ITEMS TABLE
    # =========================
    data = [["Item", "Qty", "Unit Price", "Total"]]

    for item in invoice.sales_order.items.all():
        data.append([
            item.item.name,
            str(item.quantity),
            str(item.unit_price),
            str(item.total)
        ])

    # TOTAL ROW
    data.append(["", "", "TOTAL", str(invoice.total_amount)])

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # =========================
    # FOOTER (TERMS)
    # =========================
    footer = Paragraph(
        """
        <b>Terms & Conditions</b><br/>
        Thank you for doing business with Naiberi MRF ERP.<br/>
        Goods once sold are subject to company policy.<br/>
        Payment is due as per agreement.
        """,
        styles['Normal']
    )

    elements.append(footer)

    doc.build(elements)

    return response