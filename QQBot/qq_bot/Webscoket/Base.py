from threading import Thread
from json import dumps
from threading import Thread

from mcdreforged.api.types import PluginServerInterface
from websocket import WebSocketConnectionClosedException, WebSocket

from ..Config import Config
from ..Utils import encode


class Websocket(Thread):
    flag: bool = None
    config: Config = None
    server: PluginServerInterface = None

    websocket: WebSocket = None
    websocket_uri: str = 'ws://127.0.0.1:{}/websocket/{}'

    def __init__(self, server: PluginServerInterface, config: Config, name: str):
        Thread.__init__(self, daemon=True, name=name)
        self.flag = True
        self.server = server
        self.config = config
        self.websocket_uri = self.websocket_uri.format(config.port)

    def close(self):
        if self.websocket:
            self.websocket.close()
        self.flag = False

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
            self.server.logger.warning('尝试连接到机器人失败！请检查配置或查看是否启动机器人或配置文件是否正确。')
        return False

    def handle_loop(self):
        pass

    def run(self):
        self.server.logger.info(F'线程 {self.name} 已启动！')
        while self.flag:
            self.handle_loop()
