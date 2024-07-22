from .Config import Config
from .EventSender import EventSender

from mcdreforged.api.command import SimpleCommandBuilder, GreedyText
from mcdreforged.api.all import PluginServerInterface, CommandContext, CommandSource, Info


config: Config = None
event_sender: EventSender = None


def on_load(server: PluginServerInterface, old):
    def qq(source: CommandSource, content: CommandContext):
        if config.sync_all_messages:
            source.reply('§7已启用 同步所有消息 功能！此指令已自动禁用。§7')
            return None
        player = 'Console' if source.is_console else source.player
        success = event_sender.send_message(F'[{config.name}] <{player}> {content.get("message")}')
        source.reply('§a发送消息成功！§a' if success else '§c发送消息失败！§c')

    global event_sender, config
    config = server.load_config_simple(target_class=Config)
    server.register_help_message('qq', '发送消息到 QQ 群')
    server.logger.info('正在注册指令……')
    command_builder = SimpleCommandBuilder()
    command_builder.command('!!qq <message>', qq)
    command_builder.arg('message', GreedyText)
    command_builder.register(server)
    event_sender = EventSender(server, config)


def on_info(server: PluginServerInterface, info: Info):
    if not info.is_player and '[Rcon] BotServer was connected to the server!' in info.content:
        event_sender.send_info()


def on_server_stop(server: PluginServerInterface, old):
    server.logger.info('检测到服务器关闭，正在通知机器人服务器……')
    event_sender.send_shutdown()


def on_server_startup(server: PluginServerInterface):
    server.logger.info('检测到服务器开启，正在连接机器人服务器……')
    event_sender.send_startup()


def on_user_info(server: PluginServerInterface, info: Info):
    event_sender.send_player_info(info.player, info.content)


def on_player_left(server: PluginServerInterface, player: str):
    event_sender.send_player_left(player)


def on_player_joined(server: PluginServerInterface, player: str, info):
    event_sender.send_player_joined(player)
