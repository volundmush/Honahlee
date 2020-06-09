#!/usr/bin/env python3.8

import os
import sys
import argparse
import asyncio
import uvloop


def create_parser():
    parser = argparse.ArgumentParser(description="BOO", formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("--profile", nargs=1, action="store", dest="profile", metavar="<path>", default="default",
                        help="profile folder to use. (default: 'default')")

    parser.add_argument("--init", action="store", dest="init", metavar="<bool>")



async def main():
    uvloop.install()
