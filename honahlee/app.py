#!/usr/bin/env python3.8

import os, sys, importlib
import asyncio
import uvloop
from tortoise import Tortoise


async def main():

    try:
        settings = importlib.import_module('gamedata.settings')
    except Exception:
        raise Exception("Could not import settings!")

    await Tortoise.init(**settings.DATABASE_INIT)
    await Tortoise.generate_schemas(safe=True)

    fake_app = None
    from honahlee.networking.base import NetworkManager
    from honahlee.networking.telnet import TelnetProtocol

    net_man = NetworkManager(fake_app)
    net_man.register_protocol('telnet', TelnetProtocol)
    server = await net_man.create_server('telnet', '10.0.0.226', 4100, 'telnet', False)


if __name__ == "__main__":
    new_cwd = os.environ.get('HONAHLEE_TEMPLATE')
    if not os.path.exists(new_cwd):
        raise ValueError("Improper Honahlee profile!")
    os.chdir(os.path.abspath(new_cwd))
    sys.path.insert(0, os.getcwd())

    uvloop.install()
    asyncio.run(main())
