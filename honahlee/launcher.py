#!/usr/bin/env python3.8

import os, sys, re, shutil
import argparse
import asyncio
import uvloop
import honahlee

HONAHLEE_ROOT = os.path.abspath(honahlee.__file__)
HONAHLEE_PROFILE = os.path.join(HONAHLEE_ROOT, 'profile_template')

PROFILE_PATH = None


def create_parser():
    parser = argparse.ArgumentParser(description="BOO", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--profile", nargs=1, action="store", dest="profile", metavar="<profile>", default="default")
    parser.add_argument("operation", nargs="?", action="store", metavar="<operation>", default="noop")
    return parser


def set_profile_path(args):
    global PROFILE_PATH
    reg = re.compile(r"^\w+$")
    profile_name = args.profile.lower()
    if not reg.match(profile_name):
        raise ValueError("Must stick to very simple profile names!")
    honahlee_folder = os.path.join(os.path.expanduser('~'), '.honahlee')
    if not os.path.exists(honahlee_folder):
        os.makedirs(honahlee_folder)
    PROFILE_PATH = os.path.join(honahlee_folder, profile_name)


def operation_start(args):
    pass


def operation_noop(args):
    pass


def operation_stop(args):
    pass


def operation_migrate(args):
    pass


def operation_create(args):
    if not os.path.exists(PROFILE_PATH):
        shutil.copytree(HONAHLEE_PROFILE, PROFILE_PATH)
        os.rename(os.path.join(PROFILE_PATH, 'gitignore'), os.path.join(PROFILE_PATH, '.gitignore'))


def operation_list(args):
    pass


OPERATIONS = {
    'noop': operation_noop,
    'start': operation_start,
    'stop': operation_stop,
    'migrate': operation_migrate,
    'create': operation_create,
    'list': operation_list
}


async def run_launcher():
    uvloop.install()
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()

    option = args.operation.lower()

    try:
        set_profile_path(args)
        if not (op_func := OPERATIONS.get(option, None)):
            raise ValueError(f"No operation: {option}")
        op_func(args)

    except Exception as e:
        print(f"Something done goofed: {e}")
        return


def main():
    uvloop.install()
    asyncio.run(run_launcher())
