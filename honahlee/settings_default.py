from django.conf.global_settings import *

SERVER_NAME = "Honahlee"

GAME_SLOGAN = "Adventure in Worlds of Pure Imagination"

DATABASE_INIT = {
    "db_url": "sqlite://db.sqlite3",
    "modules": {'honahlee': ['honahlee.models']}
}

APPLICATION_CORE = "honahlee.core.Application"

APPLICATION_SERVICES = {
    #'database': 'honahlee.services.database.DatabaseService',
    'network': 'honahlee.services.network.NetworkService',
    'web': 'honahlee.services.web.WebService'
}

SERVER_CLASSES = {
    'base': 'honahlee.services.network.HonahleeServerFactory'
}

PROTOCOL_CLASSES = {
    'telnet': 'honahlee.protocols.telnet.MudTelnetProtocol',
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

# Note that any Servers with TLS enabled will only be created if TLS is properly
# configured.
SERVERS = {
    'telnet': {
        'port': 4100,
        'server_class': 'base',
        'protocol_class': 'telnet',
        'tls': False
    },
    'telnet_tls': {
        'port': 4101,
        'server_class': 'base',
        'protocol_class': 'telnet',
        'tls': False
    }
}

# Django Settings
USE_TZ = True
TIME_ZONE = "Etc/UTC"

INSTALLED_APPS = []

TEMPLATES = []

MIDDLEWARE = []


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
