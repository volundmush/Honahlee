from honahlee.core import BaseConfig


class Config(BaseConfig):

    def __init__(self):
        super().__init__()
        self.name = "portal"
        self.application = "honahlee_portal.app.Application"
        self.listeners = dict()

    def setup(self):
        super().setup()
        self._config_listeners()

    def _config_listeners(self):
        self.listeners["telnet"] = {"interface": "any", "port": 7999, "protocol": "telnet"}

    def _config_classes(self):
        self.classes['services']['mudlink'] = 'honahlee_portal.app.MudLinkService'
