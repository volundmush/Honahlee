#!/usr/bin/env python3.8
import importlib
import os
import sys

import asyncio
import uvloop


from honahlee.utils.misc import import_from_module


async def main():
    # Step 1: get settings from profile.
    try:
        conf = import_from_module('appdata.config.Config')
    except Exception:
        raise Exception("Could not import config!")

    config = conf()
    config.setup()

    # Step 2: Locate application Core from settings. Instantiate
    # application core and inject settings into it.
    # This doesn't have anything to do with Twisted's own Application framework.
    core_class = import_from_module(config.application)
    app_core = core_class(config)

    # Step 3: Load application from core.
    await app_core.setup()

    # Step 4: Start everything up and run forever.
    await app_core.start()


if __name__ == "__main__":
    if (new_cwd := os.environ.get("HONAHLEE_PROFILE")):
        if not os.path.exists(new_cwd):
            raise ValueError("Improper Honahlee profile!")
        os.chdir(os.path.abspath(new_cwd))
        sys.path.insert(0, os.getcwd())

    pidfile = os.path.join('.', 'app.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))
        print(pidfile)
        print(os.getpid())

    loop = uvloop.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()

    os.remove(pidfile)
