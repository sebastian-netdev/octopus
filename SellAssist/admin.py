from django.contrib import admin
from .models import *
# Register your models here.


admin.site.register(SellAssistOrder)
admin.site.register(SellAssistProduct)
admin.site.register(SellAssistUnknownProduct)
admin.site.register(SellAssistRegisteredProduct)
admin.site.register(SellAssistCart)
admin.site.register(SellAssistAPI)
admin.site.register(SellAssistAdditionalFields)