from ..Config import Config

from mcdreforged.api.event import LiteralEvent
from mcdreforged.api.types import PluginServerInterface

from time import sleep
from threading import Thread
from json import dumps, loads
from websocket import WebSocketConnectionClosedException, WebSocket


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

    def run(self):
        self.server.logger.info('服务器监听线程已启动！')
        while True:
            sleep(self.config.reconnect_interval)
            if self.connect():
                self.server.logger.info('与机器人的连接已建立！已通知插件。')
                self.server.dispatch_event(LiteralEvent('qq_bot.websocket_connected'), (None, None))
                try:
                    while True:
                        response = None
                        message = self.websocket.recv()
                        self.server.logger.info(F'收到来自机器人的消息 {message}')
                        data = loads(message)
                        type = data.get('type')
                        data = data.get('data')
                        if type == 'command':
                            response = self.command(data)
                        elif type == 'message':
                            pass
                        elif type == 'player_list':
                            pass
                        if response:
                            self.server.logger.debug(F'向机器人发送消息 {response}')
                            self.websocket.send(dumps({'success': True, 'data': response}))
                            continue
                        self.server.logger.warning(F'无法解析的消息 {message}')
                        self.websocket.send(dumps({'success': False}))
                except (WebSocketConnectionClosedException, ConnectionError):
                    self.server.logger.warning('与机器人的连接已断开！')
                    self.server.dispatch_event(LiteralEvent('qq_bot.websocket_closed'), (None, None))

    def close(self):
        if self.websocket:
            self.websocket.close()

    def connect(self):
        self.server.logger.info('正在尝试连接到机器人……')
        try:
            self.websocket = WebSocket()
            headers = [F'token: {self.config.token}', F'name: {self.config.name}']
            self.websocket.connect(self.websocket_uri, header=headers)
            self.server.logger.info('身份验证完毕，连接到机器人成功！')
            self.websocket.send('Ok')
            return False
        except (WebSocketConnectionClosedException, ConnectionError):
            self.websocket = None
            self.server.logger.error('尝试连接到机器人失败！请检查配置或查看是否启动机器人或配置文件是否正确。')
        return False
    
    def command(self, data: dict):
        if command := data.get('command'):
            if self.server.is_rcon_running():
                return {'response': self.server.rcon_query(command)}
            self.server.execute(command)
            return {'response': '命令已发送，但由于 Rcon 未连接无返回值。'}
