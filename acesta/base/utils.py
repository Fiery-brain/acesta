def timesince_accusatifier(timesince_str):
    """
    Returns timesince in the accusative case
    :param timesince_str: str
    :return: str
    """
    return timesince_str.replace("неделя", "неделю").replace("минута", "минуту")


def timesince_cutter(timesince_str):
    """
    Returns timesince in cut down format
    :param timesince_str: str
    :return: str
    """
    return timesince_str.split(",")[0]
