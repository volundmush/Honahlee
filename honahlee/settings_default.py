SERVER_NAME = "Honahlee"

GAME_SLOGAN = "Adventure in Worlds of Pure Imagination"

DATABASE_INIT = {
    "db_url": "sqlite://db.sqlite3",
    "modules": {'honahlee': ['honahlee.models']}
}

PROTOCOLS = {
    'telnet': 'honahlee.networking.telnet.TelnetProtocol'
}

GAME_CLIENT_INTERFACE = "0.0.0.0"
SERVER_CLIENT_INTERFACE = "0.0.0.0"

# Note that any Servers with TLS enabled will only be created if TLS is properly
# configured.
SERVERS = {
    'telnet': {
        'address': GAME_CLIENT_INTERFACE,
        'port': 4100,
        'protocol': 'telnet',
        'tls': False
    },
    'telnet_tls': {
        'address': GAME_CLIENT_INTERFACE,
        'port': 4101,
        'protocol': 'telnet',
        'tls': True
    }
}

PLUGIN_PATHS = []
