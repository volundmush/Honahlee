#!/usr/bin/env python3.8

import argparse
import asyncio
import os
import sys
import re
import shutil
import subprocess
import shlex
import signal

import uvloop
import honahlee

HONAHLEE_ROOT = os.path.abspath(os.path.dirname(honahlee.__file__))
HONAHLEE_APP = os.path.join(HONAHLEE_ROOT, 'app.py')
HONAHLEE_PROFILE = os.path.join(HONAHLEE_ROOT, 'profile_template')
HONAHLEE_FOLDER = os.path.join(os.path.expanduser('~'), '.honahlee')

PROFILE_PATH = None
PROFILE_PIDFILE = None
PROFILE_PID = -1


def create_parser():
    parser = argparse.ArgumentParser(description="BOO", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--profile", nargs=1, action="store", dest="profile", metavar="<profile>", default="default")
    parser.add_argument("operation", nargs="?", action="store", metavar="<operation>", default="noop")
    return parser


def set_profile_path(args):
    global PROFILE_PATH, PROFILE_PIDFILE
    reg = re.compile(r"^\w+$")
    profile_name = args.profile.lower()
    if not reg.match(profile_name):
        raise ValueError("Must stick to very simple profile names!")
    if not os.path.exists(HONAHLEE_FOLDER):
        os.makedirs(HONAHLEE_FOLDER)
    PROFILE_PATH = os.path.join(HONAHLEE_FOLDER, profile_name)
    PROFILE_PIDFILE = os.path.join(PROFILE_PATH, "server.pid")


def ensure_running():
    global PROFILE_PID
    if not os.path.exists(PROFILE_PIDFILE):
        raise ValueError("Process is not running!")
    with open(PROFILE_PIDFILE, "r") as p:
        if not (PROFILE_PID := int(p.read())):
            raise ValueError("Process pid corrupted.")
    try:
        # This doesn't actually do anything except verify that the process exists.
        os.kill(PROFILE_PID, 0)
    except OSError:
        print("Process ID seems stale. Removing stale pidfile.")
        os.remove(PROFILE_PIDFILE)
        return False
    return True


def ensure_stopped():
    global PROFILE_PID
    if not os.path.exists(PROFILE_PIDFILE):
        return True
    with open(PROFILE_PIDFILE, "r") as p:
        if not (PROFILE_PID := int(p.read())):
            raise ValueError("Process pid corrupted.")
    try:
        os.kill(PROFILE_PID, 0)
    except OSError:
        return True
    return False


def operation_start(args):
    if not ensure_stopped():
        raise ValueError(f"Server is already running as Process {PROFILE_PID}.")
    print("LET'S START THIS THING!")
    env = os.environ.copy()
    env['HONAHLEE_PROFILE'] = PROFILE_PATH
    cmd = f"{sys.executable} {HONAHLEE_APP}"
    subprocess.Popen(shlex.split(cmd), env=env)
    if not ensure_running():
        raise ValueError("Could not launch Honahlee! Why?")


def operation_noop(args):
    pass


def operation_stop(args):
    if not ensure_running():
        raise ValueError("Server is not running.")
    os.kill(PROFILE_PID, signal.SIGTERM)
    os.remove(PROFILE_PIDFILE)
    print(f"Stopped process {PROFILE_PID}")


def operation_migrate(args):
    pass


def operation_create(args):
    if not os.path.exists(PROFILE_PATH):
        shutil.copytree(HONAHLEE_PROFILE, PROFILE_PATH)
        os.rename(os.path.join(PROFILE_PATH, 'gitignore'), os.path.join(PROFILE_PATH, '.gitignore'))
        print(f"Profile created at {PROFILE_PATH}")
    else:
        print(f"Profile at {PROFILE_PATH} already exists!")


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
