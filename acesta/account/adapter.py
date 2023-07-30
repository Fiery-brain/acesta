from allauth.account import signals
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.utils import user_field
from django.contrib import messages
from django.http import HttpResponseRedirect


class AccountAdapter(DefaultAccountAdapter):
    def post_login(
        self,
        request,
        user,
        *,
        email_verification,
        signal_kwargs,
        email,
        signup,
        redirect_url
    ):
        from allauth.account.utils import get_login_redirect_url

        response = HttpResponseRedirect(
            get_login_redirect_url(request, redirect_url, signup=signup)
        )

        if signal_kwargs is None:
            signal_kwargs = {}
        signals.user_logged_in.send(
            sender=user.__class__,
            request=request,
            response=response,
            user=user,
            **signal_kwargs,
        )

        if user.registered:
            self.add_message(
                request,
                messages.SUCCESS,
                "account/messages/logged_in.txt",
                {"user": user},
            )

        return response

    def save_user(self, request, user, form, commit=False):
        """
        Saves a new `User` instance using information provided in the
        signup form.
        """
        user = super().save_user(request, user, form, commit)
        data = form.cleaned_data
        user_field(user, "phone", data.get("phone"), "")
        if user.last_name is not None and len(user.last_name):
            user.note = user.last_name
            user.last_name = None
        user.save()
        return user
