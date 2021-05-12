import asyncio
import sys
from collections import OrderedDict
from .commands.base import CommandException
import traceback
from typing import Optional, Union, List, Set


class QueueEntry:

    def __init__(self, enactor: int, actions: str, executor: Optional[int] = None, caller: Optional[int] = None,
                 connection=None, spoof: Optional[int] = None, split=True):
        self.source = enactor
        self.enactor = enactor
        self.executor = executor if executor else enactor
        self.caller = caller if caller else enactor
        self.spoof = spoof
        self.actions = actions
        self.connection = connection
        self.parser = None
        self.semaphore_obj = None
        self.inplace = None
        self.next = None
        self.pid = None
        self.cpu_start = None
        self.cmd = None
        self.core = None
        self.split_actions = split

    def process_action(self, enactor, text):
        try:
            cmd = enactor.find_cmd(text)
            if cmd:
                cmd.core = self.core
                self.cmd = cmd
                cmd.entry = self
                cmd.parser = self.parser
                try:
                    cmd.at_pre_execute()
                    cmd.execute()
                    cmd.at_post_execute()
                except CommandException as e:
                    cmd.msg(str(e))
                except Exception as e:
                    cmd.msg(text=f"EXCEPTION: {str(e)}")
                    traceback.print_exc(file=sys.stdout)
                self.cmd = None
            else:
                enactor.msg('Huh?  (Type "help" for help.)')
        except Exception as e:
            print(f"Something foofy happened: {e}")
            traceback.print_exc(file=sys.stdout)

    def action_splitter(self, text, split=True):
        if not split:
            yield text
        else:
            remaining = text
            while len(remaining):
                result, remaining, stopped = self.parser.evaluate(remaining, noeval=True, stop_at=[';'])
                if result:
                    yield result

    def execute(self):
        if not (enactor := self.core.objects.get(self.enactor, None)):
            return 0
        if not len(self.actions):
            return 0
        self.parser = enactor.parser()
        for action in self.action_splitter(self.actions, self.split_actions):
            self.process_action(enactor, action)


class WaitAction:
    def __init__(self, queue, pid, entry, duration):
        self.queue = queue
        self.pid = pid
        self.entry = entry
        self.duration = duration

    def start(self):
        pass

    async def run(self):
        await asyncio.sleep(0.1)
        self.queue.execute(self.entry)
        self.queue.wait_queue.pop(self.pid)


class CmdQueue:
    def __init__(self, core):
        self.core = core
        self.queue_data = OrderedDict()
        self.async_queue = asyncio.Queue()
        self.wait_queue = dict()
        self.pid = 0

    def push(self, entry):
        self.pid += 1
        self.queue_data[self.pid] = entry
        self.async_queue.put_nowait(self.pid)

    def wait(self, entry, duration):
        self.pid += 1
        w = WaitAction(self, self.pid, entry, duration)
        self.wait_queue[self.pid] = w
        w.start()

    async def execute(self, entry, pid):
        entry.pid = pid
        entry.core = self.core
        entry.execute()

    async def start(self):
        while True:
            try:
                pid = await self.async_queue.get()
                if (entry := self.queue_data.pop(pid, None)):
                    await self.execute(entry, pid)
            except Exception as e:
                print(f"Oops, CmdQueue encountered Exception: {str(e)}")
