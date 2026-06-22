from django.core.management.base import BaseCommand
from finance.models import ChartOfAccount


class Command(BaseCommand):
    help = "Seed mandatory Chart of Accounts"

    def handle(self, *args, **kwargs):

        accounts = [
            ("1001", "Cash", "asset"),
            ("1002", "Bank", "asset"),
            ("1101", "Accounts Receivable", "asset"),

            ("2001", "Accounts Payable", "liability"),

            ("3001", "Capital", "equity"),

            ("4001", "Sales Revenue", "income"),
            ("4002", "Other Income", "income"),

            ("5001", "Cost of Goods Sold", "expense"),
            ("5002", "Operating Expense", "expense"),
        ]

        for code, name, acc_type in accounts:
            obj, created = ChartOfAccount.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "account_type": acc_type
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created {code} - {name}"))
            else:
                self.stdout.write(f"Exists {code} - {name}")

        self.stdout.write(self.style.SUCCESS("Chart of Accounts seeded successfully"))