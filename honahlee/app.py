#!/usr/bin/env python3.8
import importlib
import os
import sys

import asyncio
import uvloop

from honahlee.utils.misc import import_from_module

# Make sure we will be running the AsyncioReactor for Twisted with Uvloop going.
# MAX SPEED BABY


# Making sure that this is imported here so it won't try and install a different reactor
# from here on.
from twisted.internet import reactor


async def main():

    # Step 1: get settings from profile.
    try:
        settings = importlib.import_module('gamedata.settings')
    except Exception:
        raise Exception("Could not import settings!")

    # Step 2: Locate application Core from settings. Instantiate
    # application core and inject settings into it.
    # This doesn't have anything to do with Twisted's own Application framework.
    core_class = import_from_module(settings.APPLICATION_CORE)
    app_core = core_class(settings)

    # Step 3: Load application from core.
    await app_core.setup()

    # Step 4: Start everything up and run forever.
    await app_core.start()


if __name__ == "__main__":
    new_cwd = os.environ.get('HONAHLEE_PROFILE')
    print(new_cwd)
    if not os.path.exists(new_cwd):
        raise ValueError("Improper Honahlee profile!")
    os.chdir(os.path.abspath(new_cwd))
    sys.path.insert(0, os.getcwd())
    #sys.stdout = open('honah.log', 'a+')

    pidfile = os.path.join('.', 'server.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))
        print(pidfile)
        print(os.getpid())

    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()
