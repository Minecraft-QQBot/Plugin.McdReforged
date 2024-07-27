from mcdreforged.api.all import PluginServerInterface, PlayerCommandSource, CommandContext, Info
from mcdreforged.api.command import SimpleCommandBuilder, GreedyText

from .Config import Config
from .Webscoket import WebsocketListener, WebsocketSender

config: Config = None
sender: WebsocketSender = None
listener: WebsocketListener = None


def on_load(server: PluginServerInterface, old):
    def qq(source: PlayerCommandSource, content: CommandContext):
        if config.flag:
            source.reply('§7已启用 同步所有消息 功能！此指令已自动禁用。§7')
            return None
        player = source.player if source.is_player else 'Console'
        success = sender.send_synchronous_message(F'[{config.name}] <{player}> {content.get("message")}')
        source.reply('§a发送消息成功！§a' if success else '§c发送消息失败！§c')

    global listener, sender, config
    config = server.load_config_simple(target_class=Config)
    server.register_help_message('qq', '发送消息到 QQ 群')
    server.logger.info('正在注册指令……')
    command_builder = SimpleCommandBuilder()
    command_builder.command('!!qq <message>', qq)
    command_builder.arg('message', GreedyText)
    command_builder.register(server)
    listener = WebsocketListener(server, config)
    listener.start()
    sender = WebsocketSender(server, config)
    server.register_event_listener('qq_bot.websocket_closed', sender.close)
    server.register_event_listener('qq_bot.websocket_connected', sender.connect)


def on_unload(server: PluginServerInterface):
    server.logger.info('检测到插件卸载，已断开与机器人的连接！')
    sender.close()
    listener.close()


def on_server_stop(server: PluginServerInterface, old):
    server.logger.info('检测到服务器关闭，正在通知机器人服务器……')
    sender.send_shutdown()


def on_server_startup(server: PluginServerInterface):
    server.logger.info('检测到服务器开启，正在连接机器人服务器……')
    sender.send_startup()


def on_user_info(server: PluginServerInterface, info: Info):
    if info.is_player:
        sender.send_player_info(info.player, info.content)


def on_player_left(server: PluginServerInterface, player: str):
    sender.send_player_left(player)


def on_player_joined(server: PluginServerInterface, player: str, info):
    sender.send_player_joined(player)
