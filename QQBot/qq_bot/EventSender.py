from .Config import Config

from mcdreforged.api.all import PluginServerInterface

import requests
from json import dumps
from pathlib import Path


class EventSender:
    config: Config = None
    template: dict = None
    server: PluginServerInterface = None
    request_url: str = 'http://127.0.0.1:{}'

    def __init__(self, server: PluginServerInterface, config: Config):
        self.server = server
        self.config = config
        self.request_url = self.request_url.format(config.port)
        self.template = {'token': config.token, 'name': config.name}

    def __request(self, name: str, data: dict = {}):
        data = (self.template | data)
        try:
            request = requests.post(F'{self.request_url}/{name}', data=dumps(data), timeout=10)
        except Exception: return None
        if request.status_code == 200:
            response = request.json()
            if response.get('success'):
                return response

    def send_info(self):
        pid = self.server.get_server_pid_all()[-1]
        if self.__request('server/info', {'pid': pid}):
            self.server.logger.info('发送服务器信息成功！')
            return None
        self.server.logger.error('发送服务器信息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_message(self, message: str):
        data = {'message': message}
        self.server.logger.info(F'向 QQ 群发送消息 {message}')
        return self.__request('send_message', data)

    def send_startup(self):
        if rcon_info := self.read_rcon_info():
            pid = self.server.get_server_pid_all()[-1]
            if response := self.__request('server/startup', {'rcon': rcon_info, 'pid': pid}):
                self.server.logger.info('发送服务器启动消息成功！')
                self.config.sync_all_messages = response.get('sync_all_messages')
                self.server.save_config_simple(self.config)
                return None
            self.server.logger.error('发送服务器启动消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_shutdown(self):
        if self.__request('server/shutdown'):
            self.server.logger.info('发送服务器关闭消息成功！')
            return None
        self.server.logger.error('发送服务器关闭消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_info(self, player: str, message: str):
        data = {'player': player, 'message': message}
        if self.__request('player/info', data):
            self.server.logger.info(F'发送玩家 {player} 消息 {message} 成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 消息 {message} 失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_left(self, player: str):
        if self.__request('player/left', {'player': player}):
            self.server.logger.info(F'发送玩家 {player} 离开消息成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 离开消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def send_player_joined(self, player: str):
        if self.__request('player/joined', {'player': player}):
            self.server.logger.info(F'发送玩家 {player} 加入消息成功！')
            return None
        self.server.logger.error(F'发送玩家 {player} 加入消息失败！请检查配置或查看是否启动服务端，然后重试。')

    def read_rcon_info(self):
        password, port = None, None
        server_config = Path('./server/server.properties')
        if not server_config.exists():
            self.server.logger.error('服务器配置文件不存在！请联系管理员求助。')
            return None, None
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
            return None, None
        return password, port