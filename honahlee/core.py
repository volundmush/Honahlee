import ssl
import asyncio
import logging

from collections import defaultdict
from honahlee.utils import import_from_module
from logging.handlers import TimedRotatingFileHandler
from autobahn.asyncio.component import Component


class BaseConfig:

    def __init__(self):
        self.name = 'honahlee'
        self.application = 'honahlee.core.Application'
        self.classes = defaultdict(dict)
        self.interfaces = dict()
        self.tls = dict()
        self.tls_contexts = dict()
        self.log_handlers = dict()
        self.logs = dict()
        self.regex = dict()
        self.wamp_realm = "honahlee"
        self.wamp_transports = "ws://127.0.0.1:8080/ws"

    def setup(self):
        self._config_classes()
        self._config_interfaces()
        self._config_tls()
        self._init_tls_contexts()
        self._config_log_handlers()
        self._config_logs()
        self._config_regex()

    def _config_classes(self):
        """
        Meant to add all necessary classes to the classes dictionary.
        """
        pass

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
        self.interfaces["any"] = "0.0.0.0"
        self.interfaces["localhost"] = "127.0.0.1"

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

    def _config_log_handlers(self):
        for name in ('application', 'server', 'client'):
            handler = TimedRotatingFileHandler(filename=f'logs/{name}', when='D')
            self.log_handlers[name] = handler

    def _config_logs(self):
        for name in ('application', 'server', 'client'):
            log = logging.getLogger(name)
            log.addHandler(self.log_handlers[name])
            self.logs[name] = log

    def _config_regex(self):
        pass


class LauncherConfig:

    def __init__(self):
        self.applications = ["portal", "hub"]


class Application(Component):

    def __init__(self, config: BaseConfig):
        self.config = config
        super().__init__(transports=config.wamp_transports, realm=config.wamp_realm)
        self.classes = defaultdict(dict)
        self.services = dict()
        self.active = False
        self.session = None
        self.on_join(self.joined)
        self.on_leave(self.left)

    def joined(self, session, details):
        self.active = True
        self.session = session

    def left(self):
        self.active = False
        self.session = None

    async def setup(self):
        found_classes = list()
        # Import all classes from the given config object.
        for category, d in self.config.classes.items():
            for name, path in d.items():
                found = import_from_module(path)
                found.app = self
                self.classes[category][name] = found
                if hasattr(found, 'class_init'):
                    found_classes.append(found)

        for name, v in sorted(self.classes['services'].items(), key=lambda x: getattr(x[1], 'init_order', 0)):
            self.services[name] = v(self)

        for service in sorted(self.services.values(), key=lambda s: getattr(s, 'load_order', 0)):
            await service.setup()
        for cls in found_classes:
            cls.class_init()

    async def start(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        start_services = sorted(self.services.values(), key=lambda s: s.start_order)
        all_services = [service.start() for service in start_services]
        all_services.append(super().start(loop))
        await asyncio.gather(*all_services)


class BaseService:
    name = None
    init_order = 0
    setup_order = 0
    start_order = 0

    def __init__(self, app):
        self.app = app

    async def setup(self):
        pass

    async def start(self):
        pass