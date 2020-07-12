from honahlee.core import BaseService


class DatabaseService(BaseService):
    setup_order = -1000
    start_order = -1000

    def __init__(self, app):
        super().__init__(app)

    async def setup(self):
        pass
