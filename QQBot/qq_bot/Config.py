from mcdreforged.api.utils import Serializable


class Config(Serializable):
    uri: str = 'ws://127.0.0.1:8000/'
    # 服务器名称
    name: str = 'name'
    # 和机器人服务器的 token 一致
    token: str = 'YourToken'
    # 尝试重连间隔(s)
    reconnect_interval: int = 5
    # 无需管，同 .env 里的 SYNC_ALL_GAME_MESSAGE
    flag: bool = False
