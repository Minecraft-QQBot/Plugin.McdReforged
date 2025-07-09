import asyncio
from asyncio import AbstractEventLoop, Task
from typing import Optional
from threading import Thread

from mcdreforged.api.types import PluginServerInterface

from ..Config import Config
from .Sender import WebsocketSender
from .Listener import WebsocketListener


class WebsocketManager(Thread):
    task: Optional[Task] = None
    event_loop: Optional[AbstractEventLoop] = None

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
        if self.event_loop is None:
            raise RuntimeError('插件初始化失败！未找到事件循环。')
        future = asyncio.run_coroutine_threadsafe(coroutine, self.event_loop)
        try:
            return future.result(timeout=20)
        except asyncio.TimeoutError:
            return None

    def close_connection(self):
        if not (self.task and self.event_loop):
            return None
        if self.sender.connection is not None:
            self.run_coroutine(self.sender.connection.close())
        self.event_loop.stop()
    