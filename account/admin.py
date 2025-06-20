from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import CustomUser
from account.forms import CustomUserChangeForm, CustomUserCreationForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ("phone", "is_staff", "is_active",)
    list_filter = ("phone", "is_staff", "is_active",)

    readonly_fields = ("last_login", "date_joined", "password")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Personal Info", {"fields": (
            "full_name", "email", "chat_id", "date_of_birth",
            "role", "balance", "is_blocked", "is_deleted"
        )}),
        ("Permissions", {"fields": (
            "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions"
        )}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone", "full_name", "email", "chat_id", "date_of_birth",
                "role", "balance", "is_blocked", "is_staff", "is_active",
                "password1", "password2"
            ),
        }),
    )

    search_fields = ("phone", "full_name",)
    ordering = ("phone",)

