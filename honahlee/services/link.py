from honahlee.core import BaseService
from honahlee.utils.misc import import_from_module


class LinkService(BaseService):
    setup_order = -2000

    def __init__(self, app):
        super().__init__(app)
        self.links = dict()
