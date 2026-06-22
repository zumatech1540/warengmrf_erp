from django.contrib import admin
from .models import Income, Expense
from .models import Income, Department

admin.site.register(Income)
admin.site.register(Expense)
admin.site.register(Department)