#!/usr/bin/env python3.8
import os
import sys

import asyncio
import uvloop

from honahlee.utils import import_from_module


def handle_exception(loop, context):
    print("HANDLING EXCEPTION")
    print(loop)
    print(context)


async def main():
    if (new_cwd := os.environ.get("HONAHLEE_PROFILE")):
        if not os.path.exists(new_cwd):
            raise ValueError("Improper Honahlee profile!")
        os.chdir(os.path.abspath(new_cwd))
        sys.path.insert(0, os.getcwd())

    if not (app_name := os.environ.get("HONAHLEE_APPNAME")):
        raise ValueError("Improper environment variables. needs HONAHLEE_APPNAME")

    # Step 1: get settings from profile.
    try:
        conf = import_from_module(f'appdata.{app_name}.Config')
    except Exception:
        raise Exception("Could not import config!")

    config = conf()
    config.setup()

    # Step 2: Locate application Core from settings. Instantiate
    if not (core_class := import_from_module(config.application)):
        raise ValueError(f"Cannot import {app_name} from config applications")

    pidfile = os.path.join('.', f'{app_name}.pid')
    with open(pidfile, 'w') as p:
        p.write(str(os.getpid()))

    app_core = core_class(config)

    # Step 3: Load application from core.
    await app_core.setup()

    # Step 4: Start everything up and run forever.
    await app_core.start()
    os.remove(pidfile)

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main(), debug=True)
