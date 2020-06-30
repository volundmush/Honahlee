#!/usr/bin/env python3.8

import asyncio
import importlib
import os
import sys

import uvloop
from honahlee.utils.misc import import_from_module


async def main():

    # Step 1: get settings from profile.
    try:
        settings = importlib.import_module('gamedata.settings')
    except Exception:
        raise Exception("Could not import settings!")

    # Step 2: Locate application Core from settings. Instantiate
    # application core and inject settings into it.
    core_class = import_from_module(settings.APPLICATION_CORE)
    app_core = core_class(settings)

    # Step 3: Load application from core.
    await app_core.setup()

    # Step 4: Start everything up and run forever.
    await app_core.start()

if __name__ == "__main__":
    new_cwd = os.environ.get('HONAHLEE_PROFILE')
    if not os.path.exists(new_cwd):
        raise ValueError("Improper Honahlee profile!")
    os.chdir(os.path.abspath(new_cwd))
    sys.path.insert(0, os.getcwd())
    sys.stdout = open('honah.log', 'a+')

    pidfile = os.path.join('.', 'server.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))
        print(pidfile)
        print(os.getpid())

    uvloop.install()
    asyncio.run(main(), debug=True)
