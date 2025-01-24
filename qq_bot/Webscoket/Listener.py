import asyncio
from json import JSONDecodeError, dumps

import websockets
from websockets.exceptions import ConnectionClosed
from psutil import Process
from mcdreforged.api.types import PluginServerInterface


from ..Config import Config
from ..Utils import decode, encode


class WebsocketListener:
    process: Process = None

    def __init__(self, server: PluginServerInterface, config: Config):
        self.server = server
        self.config = config
        self.uri = config.uri
        if self.uri.endswith('/'):
            self.uri = self.uri[:-1]
        self.uri += '/websocket/minecraft'

    async def run(self):
        headers = encode({'token': self.config.token, 'name': self.config.name})
        headers = {'type': 'McdReforged', 'info': headers}
        while True:
            async with websockets.connect(self.uri, additional_headers=headers) as connection:
                self.server.logger.info('[Listener] 已连接到机器人服务器！')
                try:
                    async for message in connection:
                        response = await self.handle_message(decode(message))
                        if response is not None:
                            await connection.send(encode(response))
                except ConnectionClosed:
                    self.server.logger.info('[Listener] 与机器人的连接已断开！')
                except Exception as error:
                    self.server.logger.error(f'[Listener] 与机器人的连接出现错误：{error} 。')
            await asyncio.sleep(self.config.reconnect_interval)
            self.server.logger.info('[Listener] 正在尝试重新连接……')


    async def handle_message(self, data: dict):
        response = None
        self.server.logger.debug(f'[Listener] 收到来自机器人的消息 {data}')
        
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
            self.server.execute(f'tellraw @a {dumps(data)}')
            return None
            
        if response is not None:
            self.server.logger.debug(f'[Listener] 向机器人发送消息 {response}')
            return {'success': True, 'data': response}
            
        self.server.logger.warning('无法解析的消息！')
        return {'success': False}

    def execute_command(self, command: str):
        if self.server.is_rcon_running():
            return self.server.rcon_query(command)
        self.server.execute(command)
        return '[Listener] 命令已发送，但由于 Rcon 未连接无返回值。'

    def execute_mcdr_command(self, command: str):
        self.server.execute_command(command)
        return {}

    def get_player_list(self, data: dict):
        if not self.server.is_rcon_running():
            self.server.logger.warning('[Listener] Rcon 未连接，无法获取玩家列表。')
            return None
        players = self.server.rcon_query('list')
        players = players.replace(' ', '')
        if len(players := players.split(':')) == 2:
            return players[1].split(',') if players[1] else []
        return []

    def get_server_occupation(self):
        if self.process is not None:
            cpu = self.process.cpu_percent()
            ram = self.process.memory_percent()
            return cpu, ram
        return False
