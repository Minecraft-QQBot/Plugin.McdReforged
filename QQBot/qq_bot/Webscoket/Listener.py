import time
from json import JSONDecodeError, dumps
from threading import Thread

from mcdreforged.api.event import LiteralEvent
from mcdreforged.api.types import PluginServerInterface
from psutil import Process
from websocket import WebSocketConnectionClosedException

from .Base import Websocket
from ..Config import Config
from ..Utils import decode, encode


class WebsocketListener(Websocket, Thread):
    flag: bool = True
    process: Process = None

    def __init__(self, server: PluginServerInterface, config: Config):
        Thread.__init__(self, name='WebsocketListener', daemon=True)
        Websocket.__init__(self, server, config, 'minecraft')

    def run(self):
        while self.flag:
            if self.connect():
                self.server.logger.info('与机器人的连接已建立！已通知插件。')
                self.server.dispatch_event(LiteralEvent('qq_bot.websocket_connected'), (None, None))
                try:
                    while True:
                        response = None
                        data = decode(self.websocket.recv())
                        self.server.logger.info(F'收到来自机器人的消息 {data}')
                        event_type = data.get('type')
                        data = data.get('data')
                        if event_type == 'command':
                            response = self.execute_command(data)
                        elif event_type == 'mcdr_command':
                            response = self.execute_mcdr_command(data)
                        elif event_type == 'player_list':
                            response = self.get_player_list(data)
                        elif event_type == 'server_occupation':
                            response = self.get_server_occupation()
                        elif event_type == 'message':
                            self.server.execute(F'tellraw @a {dumps(data)}')
                            continue
                        if response is not None:
                            self.server.logger.debug(F'向机器人发送消息 {response}')
                            self.websocket.send(encode({'success': True, 'data': response}))
                            continue
                        self.server.logger.warning(F'无法解析的消息！')
                        self.websocket.send(encode({'success': False}))
                except (WebSocketConnectionClosedException, JSONDecodeError, ConnectionError):
                    self.server.logger.warning('与机器人的连接已断开！')
                    self.server.dispatch_event(LiteralEvent('qq_bot.websocket_closed'), (None, None))
            time.sleep(self.config.reconnect_interval)

    def execute_command(self, command: str):
        if self.server.is_rcon_running():
            return self.server.rcon_query(command)
        self.server.execute(command)
        return '命令已发送，但由于 Rcon 未连接无返回值。'

    def execute_mcdr_command(self, command: str):
        self.server.execute_command(command)
        return {}

    def get_player_list(self, data: dict):
        if not self.server.is_rcon_running():
            self.server.logger.warning('Rcon 未连接，无法获取玩家列表。')
            return None
        players = self.server.rcon_query('list')
        players = players.replace(' ', '')
        if players.startswith('Thereare'):
            if len(players := players.split(': ')) == 2:
                return players[1].split(',') if players[1] else []
            return []
        self.server.logger.warning('检测到 List 指令返回值异常，无法获取玩家列表！')
        return []

    def get_server_occupation(self):
        if self.process is not None:
            cpu = self.process.cpu_percent()
            ram = self.process.memory_percent()
            return cpu, ram
        return False
