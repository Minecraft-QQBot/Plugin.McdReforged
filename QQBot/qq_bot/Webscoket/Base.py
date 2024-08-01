from mcdreforged.api.types import PluginServerInterface
from websocket import WebSocketConnectionClosedException, WebSocket

from ..Config import Config
from ..Utils import encode


class Websocket:
    config: Config = None
    server: PluginServerInterface = None

    websocket_uri: str = None
    websocket: WebSocket = None

    def __init__(self, server: PluginServerInterface, config: Config, name: str):
        self.flag = True
        self.server = server
        self.config = config
        self.websocket_uri = config.uri
        if self.websocket_uri.endswith('/'):
            self.websocket_uri = self.websocket_uri[:-1]
        self.websocket_uri += F'/websocket/{name}'

    def close(self, *args):
        if self.websocket:
            self.websocket.close()

    def connect(self, *args):
        self.server.logger.info('正在尝试连接到机器人……')
        try:
            self.websocket = WebSocket()
            headers = {"token": self.config.token, "name": self.config.name}
            headers = ['type: McdReforged', F'info: {encode(headers)}']
            self.websocket.connect(self.websocket_uri, header=headers)
            self.server.logger.info('身份验证完毕，连接到机器人成功！')
            return True
        except (WebSocketConnectionClosedException, ConnectionError):
            self.websocket = None
            self.server.logger.warning('尝试连接到机器人失败！请检查配置或查看是否启动机器人或配置文件是否正确。')
        return False
