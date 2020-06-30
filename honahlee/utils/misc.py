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
