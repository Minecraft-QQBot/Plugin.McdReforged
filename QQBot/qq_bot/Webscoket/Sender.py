from ..Config import Config

from mcdreforged.api.all import PluginServerInterface

from pathlib import Path
from json import dumps, loads
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
        self.connect()

    def close(self, server: PluginServerInterface = None, * args):
        if self.websocket:
            self.websocket.close()

    def connect(self, server: PluginServerInterface = None, * args):
        self.server.logger.info('正在尝试连接到机器人……')
        try:
            self.websocket = WebSocket()
            self.websocket.connect(self.websocket_uri)
            self.websocket.send(dumps({'token': self.config.token, 'name': self.config.name}))
            response = loads(self.websocket.recv())
            if response.get('success'):
                self.server.logger.info('身份验证完毕，连接到 WebSocket 服务器成功！')
                return True
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
            response = loads(self.websocket.recv())
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
        if rcon_info := self.read_rcon_info():
            pid = self.server.get_server_pid_all()[-1]
            if response := self.send_data('server_startup', {'rcon': rcon_info, 'pid': pid}):
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

    def read_rcon_info(self):
        password, port = None, None
        server_config = Path('./server/server.properties')
        if not server_config.exists():
            self.server.logger.error('服务器配置文件不存在！请联系管理员求助。')
            return None
        with server_config.open('r', encoding='utf-8') as file:
            for line in file.readlines():
                if (not line) or line.startswith('#'):
                    continue
                if len(line := line.strip().split('=')) == 2:
                    key, value = line
                    if key == 'enable-rcon' and value == 'false':
                        self.server.logger.error('服务器没有开启 Rcon ！请开启 Rcon 后重试。')
                        return None
                    port = (int(value) if key == 'rcon.port' else port)
                    password = (value if key == 'rcon.password' else password)
        if not (password and port):
            self.server.logger.error('服务器配置文件中没有找到 Rcon 信息！请检查服务器配置文件后重试。')
            return None
        return password, port