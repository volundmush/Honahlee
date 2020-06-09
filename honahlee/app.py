#!/usr/bin/env python3.8


import asyncio
import uvloop
from tortoise import Tortoise


async def main():



    await Tortoise.init(
        db_url="sqlite://db.sqlite3",
        modules={'honahlee': ['honahlee.models']}
    )

    await Tortoise.generate_schemas(safe=True)
    fake_app = None
    from honahlee.networking.base import NetworkManager
    from honahlee.networking.telnet import TelnetProtocol

    net_man = NetworkManager(fake_app)
    net_man.register_protocol('telnet', TelnetProtocol)
    server = await net_man.create_server('telnet', '10.0.0.226', 4100, 'telnet', False)


if __name__ == "__main__":
    uvloop.install()
    asyncio.run_forever(main())
