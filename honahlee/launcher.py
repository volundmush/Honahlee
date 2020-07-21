#!/usr/bin/env python3.8

import argparse
import os
import sys
import shutil
import subprocess
import shlex
import signal
import importlib

import honahlee

HONAHLEE_ROOT = os.path.abspath(os.path.dirname(honahlee.__file__))
HONAHLEE_LIB = None
HONAHLEE_APP = os.path.join(HONAHLEE_ROOT, 'app.py')
HONAHLEE_PROFILE = None

LIB_LIB = None
LIB_FOLDER = None
LIB_TEMPLATE = None

PROFILE_PATH = None
PROFILE_PIDFILE = None
PROFILE_PID = -1


def create_parser():
    parser = argparse.ArgumentParser(description="BOO", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--lib", nargs=1, action="store", dest="libfolder", metavar="<library>", default='honahlee')
    parser.add_argument("--init", nargs=1, action="store", dest="init", metavar="<folder>")
    parser.add_argument("operation", nargs="?", action="store", metavar="<operation>", default="_noop")
    return parser


def set_honahlee_lib(name):
    print(f"SETTING HONAHLEE LIB TO: {name}")
    global LIB_LIB, LIB_FOLDER, LIB_TEMPLATE
    LIB_LIB = importlib.import_module(name)
    LIB_FOLDER = os.path.abspath(os.path.dirname(LIB_LIB.__file__))
    LIB_TEMPLATE = os.path.join(LIB_FOLDER, "profile_template")


def set_honahlee_lib_from_profile():
    appconfig_module = importlib.import_module('appdata.config')
    name = appconfig_module.Config.lib_name
    set_honahlee_lib(name)


def set_profile_path(args):
    global PROFILE_PATH, PROFILE_PIDFILE
    PROFILE_PATH = os.getcwd()
    if not os.path.exists(os.path.join(PROFILE_PATH, 'appdata')):
        raise ValueError("Current directory is not a valid Honahlee profile!")
    PROFILE_PIDFILE = os.path.join(PROFILE_PATH, "app.pid")


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


def operation_start(op, args, unknown):
    if not ensure_stopped():
        raise ValueError(f"Server is already running as Process {PROFILE_PID}.")
    print("LET'S START THIS THING!")
    env = os.environ.copy()
    env['HONAHLEE_PROFILE'] = PROFILE_PATH
    cmd = f"{sys.executable} {HONAHLEE_APP}"
    subprocess.Popen(shlex.split(cmd), env=env)
    if not ensure_running():
        raise ValueError("Could not launch Honahlee! Why?")


def operation_noop(op, args, unknown):
    pass


def operation_stop(op, args, unknown):
    if not ensure_running():
        raise ValueError("Server is not running.")
    os.kill(PROFILE_PID, signal.SIGTERM)
    os.remove(PROFILE_PIDFILE)
    print(f"Stopped process {PROFILE_PID}")


def operation_passthru(op, args, unknown):
    """
    God only knows what people typed here. Let Django figure it out.
    """
    try:
        launcher_module = importlib.import_module('appdata.launcher')
        launcher = launcher_module.RunOperation
    except Exception as e:
        raise Exception(f"Unsupported command {op}")

    try:
        launcher(op, args, unknown)
    except Exception as e:
        print(e)
        raise Exception(f"Could not import settings!")


def option_init(name, un_args):
    prof_path = os.path.join(os.getcwd(), name)
    if not os.path.exists(prof_path):
        #os.makedirs(prof_path)
        shutil.copytree(LIB_TEMPLATE, prof_path)
        os.rename(os.path.join(prof_path, 'gitignore'), os.path.join(prof_path, '.gitignore'))
        if (setup := getattr(LIB_LIB, 'setup_template', None)):
            setup(prof_path, un_args)
        print(f"Profile created at {prof_path}")
    else:
        print(f"Profile at {prof_path} already exists!")


CHOICES = ['start', 'stop', 'noop']

OPERATIONS = {
    '_noop': operation_noop,
    'start': operation_start,
    'stop': operation_stop,
    '_passthru': operation_passthru,
}


def main():
    parser = create_parser()
    args, unknown_args = parser.parse_known_args()

    option = args.operation.lower()
    operation = option

    if option not in CHOICES:
        option = '_passthru'

    try:
        if args.init:
            set_honahlee_lib(args.libfolder[0])
            option_init(args.init[0], unknown_args)
            option = '_noop'
            operation = '_noop'
        if option in ['start', 'stop', '_passthru']:
            set_profile_path(args)
            os.chdir(PROFILE_PATH)
            import sys
            sys.path.insert(0, os.getcwd())
            set_honahlee_lib_from_profile()

        if not (op_func := OPERATIONS.get(option, None)):
            raise ValueError(f"No operation: {option}")
        op_func(operation, args, unknown_args)

    except Exception as e:
        import sys
        import traceback
        traceback.print_exc(file=sys.stdout)
        print(f"Something done goofed: {e}")
