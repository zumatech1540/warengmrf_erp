from django.contrib import admin
from .models import WasteCategory, Supplier, WasteIntake, WastePurchase, WasteStatusHistory

# Register your models here.
admin.site.register(WasteCategory)
admin.site.register(Supplier)
admin.site.register(WasteIntake)
admin.site.register(WastePurchase)
admin.site.register(WasteStatusHistory)