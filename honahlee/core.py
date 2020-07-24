import uuid
import ssl
import asyncio

from collections import defaultdict
from honahlee.utils.misc import import_from_module


class BaseConfig:

    def __init__(self):
        self.name = 'honahlee'
        self.application = 'honahlee.core.Application'
        self.classes = defaultdict(dict)
        self.interfaces = dict()
        self.tls = dict()
        self.tls_contexts = dict()
        self.servers = defaultdict(dict)
        self.clients = defaultdict(dict)

    def setup(self):
        self._config_classes()
        self._config_interfaces()
        self._config_tls()
        self._init_tls_contexts()
        self._config_servers()
        self._config_clients()

    def _config_classes(self):
        """
        Meant to add all necessary classes to the classes dictionary.
        """
        self.classes['services']['network'] = 'honahlee.services.network.ServerService'
        self.classes['services']['client'] = 'honahlee.services.network.ClientService'
        self.classes['servers']['base'] = 'honahlee.services.network.HonahleeServer'
        self.classes['clients']['base'] = 'honahlee.services.network.HonahleeClient'

    def _config_interfaces(self):
        """
        This lets you assign a name to an interface. 'internal' is for things hosted on an
        loopback is for hosting on the host itself with no access from other computers.
        internal is for your internal network. Same as loopback unless configured otherwise.
        external is for any internet-facing adapters.
        """
        self.interfaces['loopback'] = "127.0.0.1"
        self.interfaces['internal'] = "127.0.0.1"
        self.interfaces['external'] = "0.0.0.0"

    def _config_tls(self):
        """
        can have multiple contexts for different TLS/SSL cert combos.
        These must be file paths to the certifications/keys in question.
        """
        pass

    def _init_tls_contexts(self):
        for k, v in self.tls.items():
            new_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
            new_context.load_cert_chain(v['pem'], v['key'])
            self.tls_contexts[k] = new_context

    def _config_servers(self):
        pass

    def _config_clients(self):
        pass


class BaseApplication:

    def __init__(self, config: BaseConfig):
        self.config = config
        self.classes = defaultdict(dict)
        self.services = dict()
        self.loop = asyncio.get_event_loop()

    async def setup(self):
        # Import all classes from the given config object.
        for category, d in self.config.classes.items():
            for name, path in d.items():
                found = import_from_module(path)
                found.app = self
                self.classes[category][name] = found

        for name, v in sorted(self.classes['services'].items(), key=lambda x: getattr(x[1], 'init_order', 0)):
            self.services[name] = v()

        for service in sorted(self.services.values(), key=lambda s: getattr(s, 'load_order', 0)):
            await service.setup()

    async def start(self):
        for service in sorted(self.services.values(), key=lambda s: s.start_order):
            await service.start()

    def fresh_uuid4(self, existing):
        """
        Given a list of UUID4s, generate a new one that's not already used.
        Yes, I know this is silly. UUIDs are meant to be unique by sheer statistic unlikelihood of a conflict.
        I'm just that afraid of collisions.
        """
        existing = set(existing)
        fresh_uuid = uuid.uuid4()
        while fresh_uuid in existing:
            fresh_uuid = uuid.uuid4()
        return fresh_uuid


class Application(BaseApplication):
    pass


class BaseService:
    app = None
    init_order = 0
    setup_order = 0
    start_order = 0

    async def setup(self):
        pass

    async def start(self):
        pass
