from honahlee.core import BaseConfig


class Config(BaseConfig):

    def __init__(self):
        super().__init__()
        self.name = "hub"
        self.application = "honahlee_hub.app.Application"
