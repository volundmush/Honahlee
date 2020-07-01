#!/usr/bin/env python3.8

import asyncio
import importlib
import os
import sys
import uvloop

from honahlee.utils.misc import import_from_module
from twisted.internet import ssl, asyncioreactor
from twisted.application import service

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)
asyncioreactor.install(eventloop=loop)

application = service.Application("Honahlee")

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

try:
    settings = importlib.import_module('gamedata.settings')
except Exception:
    raise Exception("Could not import settings!")
application.settings = settings

for k, v in settings.APPLICATION_SERVICES.items():
    service_class = import_from_module(v)
    service = service_class()
    service.setServiceParent(application)
