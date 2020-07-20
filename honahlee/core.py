from collections import defaultdict
import uuid
from honahlee.utils.misc import import_from_module


class BaseConfig:

    def __init__(self):
        self.name = 'honahlee'
        self.application = 'honahlee.core.Application'
        self.classes = defaultdict(dict)
        self.interfaces = dict()
        self.tls = dict()
        self.servers = defaultdict(dict)
        self.clients = defaultdict(dict)

    def setup(self):
        self._config_classes()
        self._config_interfaces()
        self._config_tls()

    def _config_classes(self):
        """
        Meant to add all necessary classes to the classes dictionary.
        """
        self.classes['services']['network'] = 'honahlee.services.network.ServerService'
        self.classes['services']['client'] = 'honahlee.services.network.ClientService'
        self.classes['servers']['base'] = 'honahlee.services.network.HonahleeServer'
        self.classes['protocols']['telnet'] = 'honahlee.protocols.telnet.TelnetAsgiProtocol'
        self.classes['consumers']['telnet'] = 'honahlee.protocols.telnet.AsyncTelnetConsumer'
        self.classes['consumers']['game'] = 'honahlee.services.web.GameConsumer'
        self.classes['consumers']['link'] = 'honahlee.services.web.LinkConsumer'
        self.classes['consumers']['lifespan'] = 'honahlee.services.web.LifespanAsyncConsumer'

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
        self.tls['default'] = {
            'cert': '',
            'key': ''
        }

    def _config_servers(self):
        pass

    def _config_clients(self):
        pass


class BaseApplication:

    def __init__(self, config):
        self.config = config
        self.classes = defaultdict(dict)
        self.services = dict()

    async def setup(self):
        # Import all classes from the given config object.
        for category, d in self.config.classes.items():
            for name, path in d.items():
                found = import_from_module(path)
                found.app = self
                self.classes[category][name] = found

        for name, v in sorted(self.classes['services'].items(), key=lambda x: getattr(x[1], 'init_order', 0)):
            self.services[name] = v(self)

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
        fresh_uuid = None
        while fresh_uuid is None:
            new_uuid = uuid.uuid4()
            if new_uuid not in existing:
                fresh_uuid = new_uuid
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
