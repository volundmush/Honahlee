import importlib


def import_from_module(path: str):
    if not path:
        raise ImportError("Cannot import null path!")
    if '.' not in path:
        raise ImportError("Path is not in dot format!")
    split_path = path.split('.')
    identifier = split_path.pop(-1)
    module = importlib.import_module('.'.join(split_path))
    return getattr(module, identifier)


def to_str(text, session=None):
    """
    Try to decode a bytestream to a python str, using encoding schemas from settings
    or from Session. Will always return a str(), also if not given a str/bytes.

    Args:
        text (any): The text to encode to bytes. If a str, return it. If also not bytes, convert
            to str using str() or repr() as a fallback.
        session (Session, optional): A Session to get encoding info from. Will try this before
            falling back to settings.ENCODINGS.

    Returns:
        decoded_text (str): The decoded text.

    Note:
        If `text` is already str, return it as is.
    """
    if isinstance(text, str):
        return text
    if not isinstance(text, bytes):
        # not a byte, convert directly to str
        try:
            return str(text)
        except Exception:
            return repr(text)

    default_encoding = session.protocol_flags.get("ENCODING", "utf-8") if session else "utf-8"
    try:
        return text.decode(default_encoding)
    except (LookupError, UnicodeDecodeError):
        from django.conf import settings
        for encoding in settings.ENCODINGS:
            try:
                return text.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        # no valid encoding found. Replace unconvertable parts with ?
        return text.decode(default_encoding, errors="replace")

