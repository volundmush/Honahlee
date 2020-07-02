from honahlee.utils.misc import import_from_module
import asyncio


class BaseApplication:

    def __init__(self, settings):
        self.settings = settings
        self.services = dict()
        self.awaitables = list()

    async def setup(self):
        for k, v in self.settings.APPLICATION_SERVICES.items():
            service_class = import_from_module(v)
            self.services[k] = service_class(self)

        for service in sorted(self.services.values(), key=lambda s: s.setup_order):
            await service.setup()

    async def start(self):
        for service in sorted(self.services.values(), key=lambda s: s.start_order):
            await service.start()

        #await asyncio.gather(*self.awaitables)


class Application(BaseApplication):
    pass


class BaseService:
    setup_order = 0
    start_order = 0

    def __init__(self, app):
        self.app = app

    async def setup(self):
        pass

    async def start(self):
        pass
