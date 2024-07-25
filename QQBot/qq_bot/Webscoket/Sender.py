from ..Config import Config

from mcdreforged.api.types import PluginServerInterface

import time
from json import dumps, loads
from threading import Thread
from websocket import WebSocketConnectionClosedException, WebSocket


class WebsocketSender:
    config: Config = None
    server: PluginServerInterface = None

    websocket: WebSocket = None
    websocket_uri: str = 'ws://127.0.0.1:{}/websocket/bot'

    def __init__(self, server: PluginServerInterface, config: Config):
        self.server = server
        self.config = config
        self.websocket_uri = self.websocket_uri.format(config.port)
        thread = Thread(name='ConnectionKeeper', target=self.keep_connection, daemon=True)
        thread.start()

    def close(self, * args):
        if self.websocket:
            self.websocket.close()

    def connect(self, * args):
        self.server.logger.info('正在尝试连接到机器人……')
        try:
            self.websocket = WebSocket()
            headers = [F'token: {self.config.token}', F'name: {self.config.name}']
            self.websocket.connect(self.websocket_uri, header=headers)
            self.server.logger.info('身份验证完毕，连接到机器人成功！')
        except (WebSocketConnectionClosedException, ConnectionError):
            self.websocket = None
            self.server.logger.error('连接到机器人失败！请检查配置或查看是否启动机器人或配置文件是否正确，然后重试。')
        return False

    def send_data(self, type: str, data: dict = {}, retry: bool = True):
        if retry: data = {'type': type, 'data': data}
        if not self.websocket:
            if not self.connect():
                self.server.logger.warn('与机器人服务器的链接已断开，无法发送数据！')
                return None
            self.server.logger.info('检测到链接关闭，已重新连接到机器人！')
        try:
            self.websocket.send(dumps(data))
            message = self.websocket.recv()
            self.server.logger.info(F'收到来自机器人的消息 {message}')
            response = loads(message)
        except (WebSocketConnectionClosedException, ConnectionError):
            self.websocket = None
            self.server.logger.warn('与机器人的连接已断开！正在尝试重连')
            for _ in range(3):
                if self.connect() and retry:
                    return self.send_data(type, data, retry=False)
            return None
        self.server.logger.debug(F'来自机器人的回应 {response}！')
        if response.get('success'):
            return response if (response := response.get('data', True)) else True
        self.server.logger.warn(F'向 WebSocket 服务器发送 {type} 事件失败！请检查机器人。')

    def send_pid(self):
        pid = self.server.get_server_pid_all()[-1]
        if self.send_data('server_pid', {'pid': pid}):
            self.server.logger.info('发送服务器信息成功！')
            return None
        self.server.logger.error('发送服务器信息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_synchronous_message(self, message: str):
        data = {'message': message}
        self.server.logger.info(F'向 QQ 群发送消息 {message}')
        return self.send_data('message', data)

    def send_startup(self):
        pid = self.server.get_server_pid_all()[-1]
        if response := self.send_data('server_startup', {'pid': pid}):
            self.server.logger.info('发送服务器启动消息成功！')
            self.config.flag = response.get('flag', False)
            self.server.logger.info(F'保存同步的配置 {self.config}')
            self.server.save_config_simple(self.config)
            return None
        self.server.logger.error('发送服务器启动消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_shutdown(self):
        if self.send_data('server_shutdown'):
            self.server.logger.info('发送服务器关闭消息成功！')
            return None
        self.server.logger.error('发送服务器关闭消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_info(self, player: str, message: str):
        data = {'player': player, 'message': message}
        if self.send_data('player_info', data):
            self.server.logger.info(F'发送玩家 {player} 消息 {message} 成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 消息 {message} 失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_left(self, player: str):
        if self.send_data('player_left', {'player': player}):
            self.server.logger.info(F'发送玩家 {player} 离开消息成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 离开消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_joined(self, player: str):
        if self.send_data('player_joined', {'player': player}):
            self.server.logger.info(F'发送玩家 {player} 加入消息成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 加入消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def keep_connection(self):
        while True:
            time.sleep(60)
            if self.websocket:
                try:
                    self.websocket.ping()
                except (WebSocketConnectionClosedException, ConnectionError):
                    self.websocket = None
                    self.server.logger.warn('与机器人的连接已断开！')
