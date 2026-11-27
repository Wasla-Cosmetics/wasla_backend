from unfold.forms import (
    UserChangeForm as UnfoldUserChangeForm,
)
from unfold.forms import (
    UserCreationForm as UnfoldUserCreationForm,
)

from apps.authentication.models import User


class WaslaUserCreationForm(UnfoldUserCreationForm):
    class Meta(UnfoldUserCreationForm.Meta):
        model = User
        fields = ("phone", "email", "full_name")


class WaslaUserChangeForm(UnfoldUserChangeForm):
    class Meta:
        model = User
        fields = "__all__"
