import asyncio
from asyncio import AbstractEventLoop, Task
from threading import Thread

from mcdreforged.api.types import PluginServerInterface

from ..Config import Config
from .Sender import WebsocketSender
from .Listener import WebsocketListener


class WebsocketManager(Thread):
    task: Task = None
    event_loop: AbstractEventLoop = None

    def __init__(self, server: PluginServerInterface, config: Config):
        Thread.__init__(self, name='WebsocketManager', daemon=True)
        self.server = server
        self.sender = WebsocketSender(server, config)
        self.listener = WebsocketListener(server, config)

    def run(self):
        self.event_loop = asyncio.new_event_loop()
        self.event_loop.create_task(self.sender.connect())
        self.task = self.event_loop.create_task(self.listener.run())
        self.event_loop.run_forever()

    def run_coroutine(self, coroutine):
        future = asyncio.run_coroutine_threadsafe(coroutine, self.event_loop)
        return future.result()

    def close_connection(self):
        self.task.cancel()
        if self.sender.connection is not None:
            self.run_coroutine(self.sender.connection.close())
            self.event_loop.stop()
            return None
        self.event_loop.stop()
        