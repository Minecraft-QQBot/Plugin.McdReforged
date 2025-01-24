import asyncio
from json import JSONDecodeError

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.asyncio.client import ClientConnection
from mcdreforged.api.types import PluginServerInterface

from ..Config import Config
from ..Utils import decode, encode


class WebsocketSender:
    connection: ClientConnection = None

    def __init__(self, server: PluginServerInterface, config: Config):
        self.server = server
        self.config = config
        self.uri = config.uri
        if self.uri.endswith('/'):
            self.uri = self.uri[:-1]
        self.uri += '/websocket/bot'

    async def connect(self):
        if self.connection:
            return True
        headers = encode({'token': self.config.token, 'name': self.config.name})
        headers = {'type': 'McdReforged', 'info': headers}
        try:
            self.connection = await websockets.connect(self.uri, additional_headers=headers)
            self.server.logger.info('[Sender] 已连接到机器人服务器！')
            return True
        except InvalidStatus:
            self.server.logger.warning(f'[Sender] 服务器拒绝请求！可能是因为口令不正确，请确保正确填写。')
        except (ConnectionRefusedError, ConnectionError):
            self.server.logger.warning('[Sender] 无法连接到机器人服务器！')
            return False

    async def send_data(self, event_type: str, data=None, wait_response: bool = True):
        message_data = {'type': event_type}
        if data is not None:
            message_data['data'] = data
        if self.connection is None:
            if not await self.connect():
                return None
        try:
            await self.connection.send(encode(message_data))
            self.server.logger.debug(f'[Sender] 发送 {message_data} 事件成功！')
            if not wait_response:
                return True
            self.server.logger.debug('等待来自机器人的回应……')
            response = decode(await self.connection.recv())
            self.server.logger.info(f'[Sender] 收到来自机器人的消息 {response}')
            if response.get('success'):
                return response.get('data', True)
            self.server.logger.warning(f'[Sender] 向服务器发送 {event_type} 事件失败！请检查机器人。')
            return None
        except JSONDecodeError:
            self.server.logger.warning(f'[Sender] 向服务器发送 {event_type} 事件失败！服务器返回了非法的 JSON 数据。')
            return None
        except ConnectionClosed:
            self.connection = None
            self.server.logger.warning(f'[Sender] 与机器人的连接已断开！正在尝试重连。')
            if await self.connect():
                return await self.send_data(event_type, data)
            return None

    async def send_player_chat(self, player: str, message: str):
        self.server.logger.info(f'[Sender] 发送玩家 {player} 的聊天消息: {message}')
        return await self.send_data('player_chat', (player, message), wait_response=False)

    async def send_synchronous_message(self, message: str):
        self.server.logger.info(f'[Sender] 向 QQ 群发送消息 {message}')
        return await self.send_data('message', message)

    async def send_startup(self):
        if response := await self.send_data('server_startup'):
            self.server.logger.info('[Sender] 发送服务器启动消息成功！')
            return None
        self.server.logger.error('[Sender] 发送服务器启动消息失败！请检查配置或查看是否启动服务端，然后重试。')

    async def send_shutdown(self):
        if await self.send_data('server_shutdown'):
            self.server.logger.info('[Sender] 发送服务器关闭消息成功！')
            return None
        self.server.logger.error('[Sender] 发送服务器关闭消息失败！请检查配置或查看是否启动服务端，然后重试。')

    async def send_player_left(self, player: str):
        if await self.send_data('player_left', player):
            self.server.logger.info(f'[Sender] 发送玩家 {player} 离开消息成功！')
            return None
        self.server.logger.error(f'[Sender] 发送玩家 {player} 离开消息失败！请检查配置或查看是否启动服务端，然后重试。')

    async def send_player_joined(self, player: str):
        if await self.send_data('player_joined', player):
            self.server.logger.info(f'[Sender] 发送玩家 {player} 加入消息成功！')
            return None
        self.server.logger.error(f'[Sender] 发送玩家 {player} 加入消息失败！请检查配置或查看是否启动服务端，然后重试。')
