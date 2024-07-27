import time
from threading import Thread
from json import JSONDecodeError, dumps, loads
from websocket import WebSocketConnectionClosedException, WebSocket

from mcdreforged.api.event import LiteralEvent
from mcdreforged.api.types import PluginServerInterface

from ..Config import Config
from ..Utils import decode, encode


class WebsocketListener(Thread):
    config: Config = None
    server: PluginServerInterface = None

    websocket: WebSocket = None
    websocket_uri: str = 'ws://127.0.0.1:{}/websocket/minecraft'

    def __init__(self, server: PluginServerInterface, config: Config):
        Thread.__init__(self, name='WebsocketListener', daemon=True)
        self.server = server
        self.config = config
        self.websocket_uri = self.websocket_uri.format(config.port)

    def close(self):
        if self.websocket:
            self.websocket.close()
        exit()

    def connect(self):
        self.server.logger.info('正在尝试连接到机器人……')
        try:
            self.websocket = WebSocket()
            headers = {"token": self.config.token, "name": self.config.name}
            headers = ['type: McdReforged', F'info: {encode(dumps(headers))}']
            self.websocket.connect(self.websocket_uri, header=headers)
            self.server.logger.info('身份验证完毕，连接到机器人成功！')
            self.websocket.send('Ok')
            return True
        except (WebSocketConnectionClosedException, ConnectionError):
            self.websocket = None
            self.server.logger.error('尝试连接到机器人失败！请检查配置或查看是否启动机器人或配置文件是否正确。')
        return False

    def run(self):
        self.server.logger.info('服务器监听线程已启动！')
        while True:
            if self.connect():
                self.server.logger.info('与机器人的连接已建立！已通知插件。')
                self.server.dispatch_event(LiteralEvent('qq_bot.websocket_connected'), (None, None))
                try:
                    while True:
                        response = None
                        message = decode(self.websocket.recv())
                        self.server.logger.info(F'收到来自机器人的消息 {message}')
                        data = loads(message)
                        event_type = data.get('type')
                        data = data.get('data')
                        if event_type == 'command':
                            response = self.command(data)
                        elif event_type == 'mcdr_command':
                            response = self.mcdr_command(data)
                        elif event_type == 'message':
                            pass
                        elif event_type == 'player_list':
                            self.player_list(data)
                        if response is not None:
                            self.server.logger.debug(F'向机器人发送消息 {response}')
                            self.websocket.send(encode(dumps({'success': True, 'data': response})))
                            continue
                        self.server.logger.warning(F'无法解析的消息 {message}')
                        self.websocket.send(encode(dumps({'success': False})))
                except (WebSocketConnectionClosedException, JSONDecodeError, ConnectionError):
                    self.server.logger.warning('与机器人的连接已断开！')
                    self.server.dispatch_event(LiteralEvent('qq_bot.websocket_closed'), (None, None))
            time.sleep(self.config.reconnect_interval)

    def command(self, data: dict):
        if command := data.get('command'):
            if self.server.is_rcon_running():
                return {'response': self.server.rcon_query(command)}
            self.server.execute(command)
            return {'response': '命令已发送，但由于 Rcon 未连接无返回值。'}

    def mcdr_command(self, data: dict):
        if command := data.get('command'):
            self.server.execute_command(command)
            return {}

    def player_list(self, data: dict):
        if not self.server.is_rcon_running():
            return None
        players = self.server.rcon_query('list')
        players = players.replace(' ', '')
        if len(players := players.split(':')) == 2:
            return {'players': players[1].split(',') if players[1] else []}
        return []
