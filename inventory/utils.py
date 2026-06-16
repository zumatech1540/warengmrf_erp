from datetime import datetime

def generate_supplier_invoice():

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"INV-{timestamp}"



def generate_po_number():
    return "PO-" + datetime.now().strftime("%Y%m%d%H%M%S")