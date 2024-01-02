def get_height_base(content_height: str) -> int:
    """
    Returns base height according to client height
    :param content_height: str
    :return: int
    """
    return (
        int(
            (int(content_height) - 140)
            * (int(content_height) - 168)
            / int(content_height)
        )
        - 20
    )
