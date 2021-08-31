import re
import time

from core import AmiyaBot, Message, Chain
from core.util.config import config
from core.database.models import User, Message as MessageBase

from .admin.groupAdmin import group_admin_handler
from .normal.nlp import natural_language_processing
from .normal.face import get_face
from .user.emotion import emotion
from .user.greeting import greeting
from .user.userInfo import UserInfo
from .user.intellectAlarm import IntellectAlarm
from .menu.menu import Menu
from .weibo.weibo import WeiBo
from .arknights import Arknights

limit = config('message.limit')
account = config('selfId')
close_beta = config('closeBeta')


class Handlers:
    def __init__(self, bot: AmiyaBot):
        self.bot = bot
        self.arknights = Arknights(bot)
        self.functions = [
            Menu(),
            WeiBo(),
            UserInfo(),
            IntellectAlarm()
        ]

    def reply_group_message(self, data: Message):
        if data.is_only_call:
            return Chain(data).dont_at().image(get_face())

        if data.is_call or data.user_info.waiting:
            for func in self.functions:
                if func.check(data):
                    return func.action(data)

            ark_result = self.arknights.find_results(data)
            if ark_result:
                return ark_result

            for action in [emotion, natural_language_processing]:
                result = action(data)
                if result:
                    return result

        return greeting(data)

    def reply_private_message(self, data: Message):
        message = data.text
        reply = Chain(data)

        if '关闭报错推送' in message:
            self.bot.send_err = False
            return reply.text('已关闭报错推送')

        if '强制更新' in message:
            self.bot.send_to_admin('开始强制更新...')
            self.arknights.download_bot_resource(True)
            self.arknights.reset_ignore(True)
            self.bot.restart()
            return reply.text('即将重新启动...')

        if '重启' in message:
            self.bot.restart()
            return reply.text('即将重新启动...')

        if '屏蔽' in message:
            s = 0 if '解除' in message else 1
            r = re.search(r'(\d+)', message)
            if r:
                mute_id = int(r.group(1))
                if mute_id == data.user_id:
                    return reply.text('不能操作您自己...')
                user = User.get_or_none(user_id=mute_id)
                if user:
                    User.update(black=s).where(User.user_id == mute_id).execute()
                    return reply.text(f'已{"屏蔽" if s else "解除"}用户【{mute_id}】')
                else:
                    return reply.text(f'没有找到用户【{mute_id}】')

    def event_handler(self, data: Message):
        event_name = data.event_name
        message = data.message

        if event_name == 'BotReloginEvent':
            self.bot.send_to_admin('重新登陆')

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

    def filter_handler(self, data: Message):
        if data.is_admin is False and data.type == 'friend':
            return False

        if data.group_id and close_beta['enable']:
            if str(data.group_id) != str(close_beta['groupId']):
                return False

        for item in ['Q群管家', '小冰']:
            if item in data.text:
                return False

        if data.is_black:
            return False

        speed = MessageBase.select().where(
            MessageBase.user_id == account,
            MessageBase.target_id == data.user_id,
            MessageBase.msg_time >= time.time() - limit['seconds']
        )
        if speed.count() >= limit['maxCount']:
            return Chain(data).dont_at().text('博士说话太快了，请慢一些吧～')

        return self.group_admin_handler(data) if data.type == 'group' else True

    @staticmethod
    def group_admin_handler(data: Message):
        return group_admin_handler(data)
