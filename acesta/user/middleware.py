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
