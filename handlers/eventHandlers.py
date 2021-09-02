from core import AmiyaBot, Message, Chain
from handlers.normal.touch import get_random_reply
from dataSource.wiki import Wiki


class EventHandlers:
    def __init__(self, bot: AmiyaBot):
        self.bot = bot
        self.wiki = Wiki()

    def event_handler(self, data: Message):
        event_name = data.event_name
        message = data.message

        if event_name == 'BotReloginEvent':
            self.bot.send_to_admin('重新登陆')

        if event_name == 'NudgeEvent' and message['target'] == self.bot.account:
            data.type = 'group'
            data.group_id = message['subject']['id']
            self.bot.send_message(
                get_random_reply(data)
            )

        if event_name == 'MemberJoinEvent':
            data.type = 'group'
            data.user_id = message['member']['id']
            data.group_id = message['member']['group']['id']
            data.nickname = message['member']['memberName']
            self.bot.send_message(
                Chain(data).text(f'欢迎新博士{data.nickname}~，我是阿米娅，请多多指教哦')
            )

        if event_name == 'BotJoinGroupEvent':
            data.type = 'group'
            data.group_id = message['group']['id']
            self.bot.send_message(
                Chain(data).text('博士，初次见面，这里是阿米娅2号，姐姐去了很远的地方，今后就由我来代替姐姐的工作吧，请多多指教哦')
            )

        if event_name == 'BotInvitedJoinGroupRequestEvent':
            self.bot.http.handle_join_group(message)

        if event_name in ['BotMuteEvent', 'BotLeaveEventKick']:
            if 'operator' in message:
                message = message['operator']
            group_id = message['group']['id']

            self.bot.http.leave_group(
                group_id=group_id,
                flag=event_name == 'BotMuteEvent'
            )
            self.bot.send_to_admin(f'已退出群{group_id}，原因：{event_name}')
