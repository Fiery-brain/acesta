from acesta.user.models import User


def user_display(user: User):
    """
    Returns user's representation
    :param user: User
    :return: str
    """
    return f"{ user.first_name } { user.middle_name }".strip()
