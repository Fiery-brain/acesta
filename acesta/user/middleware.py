from django.shortcuts import redirect


def clean_up_old_periods(get_response):
    def middleware(request):
        response = get_response(request)
        if request.user.is_authenticated:
            request.user.clean_up_old_periods()
        return response

    return middleware


def set_last_hit(get_response):
    def middleware(request):
        response = get_response(request)
        if request.user.is_authenticated:
            request.user.set_last_hit()
        return response

    return middleware


def check_registered(get_response):
    def middleware(request):
        response = get_response(request)
        if (
            request.user.is_authenticated
            and not request.user.registered
            and request.resolver_match.view_name != "account_signupnext"
        ):
            response = redirect("account_signupnext")
        return response

    return middleware
