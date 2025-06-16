from django.contrib import admin

from .models import Visa,VisaRegister


# Register your models here.
@admin.register(Visa)
class visaAdmin(admin.ModelAdmin):
    list_display = ["name","created_at"]
    list_filter = ["created_at"]
    search_fields = ["name"]

@admin.register(VisaRegister)
class visaRegisterAdmin(admin.ModelAdmin):
    list_display = ["user__full_name","visa__name","visa_unique_code","created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__full_name","visa__name","visa_unique_code"]