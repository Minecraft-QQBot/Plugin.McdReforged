from mcdreforged.api.utils import Serializable


class Config(Serializable):
    # 机器人服务器的端口
    port: int = 8000
    # 服务器名称
    name: str = 'name'
    # 和机器人服务器的 token 一致
    token: str = 'YourToken'
    # 无需管，同 .env 里的 SYNC_ALL_GAME_MESSAGE
    flag: bool = False
