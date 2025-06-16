from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

from account.models import CustomUser

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "full_name", "email", "date_of_birth", "role",
            "balance", "chat_id", "is_blocked",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].required = True
        self.fields["password2"].required = True

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            "phone", "password",  # required
            "full_name", "email", "chat_id", "date_of_birth",
            "role", "balance", "is_blocked", "is_deleted",
            "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
            "last_login", "date_joined",
        )