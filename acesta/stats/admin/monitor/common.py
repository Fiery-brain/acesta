def sort_monitor(monitor, column) -> dict:
    """
    Sorts monitor dict by column
    :param monitor: dict
    :param column: str
    :return: dict
    """
    return dict(
        sorted(
            monitor.items(),
            key=lambda x: x[1].get(column),
            reverse=True if column != "code" else False,
        )
    )
