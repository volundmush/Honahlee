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
