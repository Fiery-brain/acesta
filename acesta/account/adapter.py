from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=False):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        user = super().save_user(request, user, form, commit)
        data = form.cleaned_data
        user_field(user, "middle_name", data.get("middle_name", ""))
        user_field(user, "company", data.get("company"), "")
        user_field(user, "position", data.get("position"), "")
        user_field(user, "phone", data.get("phone"), "")
        setattr(user, "region_id", getattr(data.get("region"), "code", None))
        setattr(user, "city_id", getattr(data.get("city"), "id", None))
        user.save()
        return user
