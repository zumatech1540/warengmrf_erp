from django.core.management.base import BaseCommand
from core.models import Department
from waste_management.models import WasteCategory

class Command(BaseCommand):
    help = "Bootstrap ERP system (Departments + Waste Categories)"

    def handle(self, *args, **kwargs):
        # Departments with their codes
        department_map = {
            "waste": "WST",
            "inventory": "INV",
            "finance": "FIN",
            "hr": "HR",
            "admin": "ADM",
            "collection": "COL"
        }

        for name, code in department_map.items():
            obj, created = Department.objects.get_or_create(
                name=name,
                defaults={'code': code}
            )
            self.stdout.write(self.style.SUCCESS(
                f"Department: {name} ({code}) {'CREATED' if created else 'EXISTS'}"
            ))

        # Waste Categories
        categories = ["Plastics", "Metals", "Paper", "Glass", "Organic", "Rubber", "E-waste"]
        for c in categories:
            obj, created = WasteCategory.objects.get_or_create(name=c)
            self.stdout.write(self.style.SUCCESS(
                f"Category: {c} {'CREATED' if created else 'EXISTS'}"
            ))

        self.stdout.write(self.style.SUCCESS("\n🚀 ERP Bootstrap Completed Successfully!"))