import django


def RunOperation(op, args, unknown_args):
    from . config import Config
    gameconf = Config()
    gameconf.setup()

    django.core.management.call_command(*([op] + unknown_args))
