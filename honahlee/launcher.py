#!/usr/bin/env python3.8

import asyncio
import uvloop


async def main():
    print("HELLO WORLD!")
    fake_app = None
    from honahlee.networking.base import NetworkManager, GameClientProtocol

    net_man = NetworkManager(fake_app)
    net_man.register_protocol('telnet', GameClientProtocol)
    server = await net_man.create_server('telnet', '10.0.0.226', 4100, 'telnet', False)
    print(server)

    print("WE RUNNING?!")
    await server.serve_forever()

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
    print("WE FINISHED?")
