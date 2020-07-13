from django.conf.global_settings import *

GAME_NAME = "Honahlee"
GAME_SLOGAN = "Adventure in Worlds of Pure Imagination"

# This class is used as the m entry point for all of the game code.
APPLICATION_CORE = "honahlee.core.Application"

# Honahlee is designed to be modular. Just add keys->Class paths to add
# 'services' that will be integrated into the startup process.
APPLICATION_SERVICES = {
    'database': 'honahlee.services.database.DatabaseService',
    'network': 'honahlee.services.network.NetworkService',
    'web': 'honahlee.services.web.WebService'
}

# Server Classes are containers for asyncio.create_server Server objects
# it, used by the Network Service. The base class should be fine enough
# but these can be added to and used by specific/special protocols if desired.
SERVER_CLASSES = {
    'base': 'honahlee.services.network.HonahleeServer'
}

# The Protocol Classes are used by the Network Service and Server Classes. These are
# meant to then connect to an ASGI Application.
PROTOCOL_CLASSES = {
    'telnet': 'honahlee.protocols.telnet.TelnetAsgiProtocol',
}


# CONSUMER CLASSES are used for putting together the Django Channels configuration.
CONSUMER_CLASSES = {
    'telnet': 'honahlee.protocols.telnet.AsyncTelnetConsumer',
    'game': 'honahlee.services.web.GameConsumer',
    'link': 'honahlee.services.web.LinkConsumer',
    'lifespan': 'honahlee.services.web.LifespanAsyncConsumer'
}

# The interface that the server will bind to, and the port for web services.
# Keep in mind that 80 requires running as root.
INTERFACE = "10.0.0.226"
WEB_PORT = 8001

# This needs to contain a path to your TLS certificate to enable TLS.
TLS = {
    'cert': '',
    'key': ''
}

# The Server definitions that the network service will launch using the given
# server class and protocol class.
# Note that any Servers with TLS enabled will only be created if TLS is properly
# configured.
SERVERS = {
    'telnet': {
        'port': 4100,
        'server_class': 'base',
        'protocol_class': 'telnet',
        'tls': False
    }
}

# ------------------- DJANGO SETTINGS -------------

USE_TZ = True
TIME_ZONE = "Etc/UTC"

INSTALLED_APPS = [
    "channels",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.admin",
    "django.contrib.admindocs",
    "django.contrib.flatpages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "django.contrib.messages",
    "rest_framework",
    "django_filters",
    "sekizai",
    'honahlee'
]

AUTH_USER_MODEL = "honahlee.Account"

TEMPLATES = []

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",  # 1.4?
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.admindocs.middleware.XViewMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]

MEDIA_ROOT = ''
MEDIA_URL = ''

STATIC_ROOT = None
STATIC_URL = None
STATICFILES_DIRS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "game.sqlite3",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    }
}

######################################################################
# Color Settings - Copied from Evennia
######################################################################
# Mapping to extend Evennia's normal ANSI color tags. The mapping is a list of
# tuples mapping the exact tag (not a regex!) to the ANSI convertion, like
# `(r"%c%r", ansi.ANSI_RED)` (the evennia.utils.ansi module contains all
# ANSI escape sequences). Default is to use `|` and `|[` -prefixes.
COLOR_ANSI_EXTRA_MAP = []
# Extend the available regexes for adding XTERM256 colors in-game. This is given
# as a list of regexes, where each regex must contain three anonymous groups for
# holding integers 0-5 for the red, green and blue components Default is
# is r'\|([0-5])([0-5])([0-5])', which allows e.g. |500 for red.
# XTERM256 foreground color replacement
COLOR_XTERM256_EXTRA_FG = []
# XTERM256 background color replacement. Default is \|\[([0-5])([0-5])([0-5])'
COLOR_XTERM256_EXTRA_BG = []
# Extend the available regexes for adding XTERM256 grayscale values in-game. Given
# as a list of regexes, where each regex must contain one anonymous group containing
# a single letter a-z to mark the level from white to black. Default is r'\|=([a-z])',
# which allows e.g. |=k for a medium gray.
# XTERM256 grayscale foreground
COLOR_XTERM256_EXTRA_GFG = []
# XTERM256 grayscale background. Default is \|\[=([a-z])'
COLOR_XTERM256_EXTRA_GBG = []
# ANSI does not support bright backgrounds, so Evennia fakes this by mapping it to
# XTERM256 backgrounds where supported. This is a list of tuples that maps the wanted
# ansi tag (not a regex!) to a valid XTERM256 background tag, such as `(r'{[r', r'{[500')`.
COLOR_ANSI_XTERM256_BRIGHT_BG_EXTRA_MAP = []
# If set True, the above color settings *replace* the default |-style color markdown
# rather than extend it.
COLOR_NO_DEFAULT = False
