from honahlee.utils.ansi import ANSIString


def connect_screen(viewer):
    """

    Args:
        viewer (AsyncGameConsumerMixin):

    Returns:
        The string that will be shown to people connecting to the game.
    """
    return ANSIString("|rINSERT CONNECT HERE!|n")
