from honahlee.core import BaseService
from tortoise import Tortoise


class DatabaseService(BaseService):
    setup_order = -1000
    start_order = -1000

    def __init__(self, app):
        super().__init__(app)

    async def setup(self):
        await Tortoise.init(**self.app.settings.DATABASE_INIT)
        await Tortoise.generate_schemas(safe=True)
