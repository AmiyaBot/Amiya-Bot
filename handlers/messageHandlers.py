import re
import time

from core import AmiyaBot, Message, Chain
from core.util.config import config
from core.util.common import random_code
from core.database.models import User, Admin, Message as MessageBase

from .admin.groupAdmin import group_admin_handler
from .normal.nlp import natural_language_processing
from .normal.touch import get_random_reply
from .user.emotion import emotion
from .user.greeting import greeting
from .user.userInfo import UserInfo
from .user.intellectAlarm import IntellectAlarm
from .menu.menu import Menu
from .weibo.weibo import WeiBo
from .arknights import Arknights
from .eventHandlers import EventHandlers

limit = config('message.limit')
account = config('selfId')
close_beta = config('closeBeta')


class Handlers(EventHandlers):
    def __init__(self, bot: AmiyaBot):
        super().__init__(bot)

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
            return get_random_reply(data)

        if data.is_call or data.user_info.waiting:
            ark_result = self.arknights.find_results(data)
            if ark_result:
                return ark_result

            for func in self.functions:
                if func.check(data):
                    return func.action(data)

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

        if '管理员' in message:
            r = re.search(r'(\d+)', message)
            if r:
                user_id = int(r.group(1))
                user = Admin.get_or_none(user_id=user_id)
                if '注册' in message and not user:
                    password = random_code(10)
                    Admin.create(user_id=user_id, password=password)
                    return reply.text(f'管理员{user_id}注册成功，初始密码：{password}')
                if not user:
                    return reply.text(f'没有找到管理员【{user_id}】')
                if '禁用' in message:
                    Admin.update(active=0).where(Admin.user_id == user_id).execute()
                    return reply.text(f'禁用管理员【{user_id}】')
                if '启用' in message:
                    Admin.update(active=1).where(Admin.user_id == user_id).execute()
                    return reply.text(f'启用管理员【{user_id}】')

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
