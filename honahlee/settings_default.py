SERVER_NAME = "Honahlee"

GAME_SLOGAN = "Adventure in Worlds of Pure Imagination"

DATABASE_INIT = {
    "db_url": "sqlite://db.sqlite3",
    "modules": {'honahlee': ['honahlee.models']}
}

APPLICATION_CORE = "honahlee.core.Application"
APPLICATION_SERVICES = {
    'database': 'honahlee.services.database.DatabaseService',
    'network': 'honahlee.services.network.NetworkService'
}

SERVER_CLASSES = {
    'base': 'honahlee.services.network.BaseServer'
}

PROTOCOL_CLASSES = {
    'base': 'honahlee.protocols.base.BaseProtocol',
    'telnet': 'honahlee.protocols.telnet.TelnetProtocol'
}

GAME_CLIENT_INTERFACE = "0.0.0.0"
SERVER_CLIENT_INTERFACE = "0.0.0.0"

# This needs to contain a path to your TLS certificate to enable TLS.
TLS = {
    'cert': '',
    'key': ''
}

# Note that any Servers with TLS enabled will only be created if TLS is properly
# configured.
SERVERS = {
    'telnet': {
        'address': GAME_CLIENT_INTERFACE,
        'port': 4100,
        'server_class': 'base',
        'protocol_class': 'telnet',
        'tls': False
    },
    'telnet_tls': {
        'address': GAME_CLIENT_INTERFACE,
        'port': 4101,
        'server_class': 'base',
        'protocol_class': 'telnet',
        'tls': True
    }
}

PLUGIN_PATHS = []
