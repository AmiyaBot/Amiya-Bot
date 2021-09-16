import re
import time

from core import AmiyaBot, Message, Chain
from core.util.config import config
from core.util.common import random_code, word_in_sentence
from core.database.models import User, Admin, Message as MessageBase

from handlers.functions import FunctionIndexes, manager_handler, random_reply, greeting
from handlers.handleWaiting import waiting_event

limit = config.message.limit
account = config.account.bot


class Handlers(FunctionIndexes):
    def __init__(self, bot: AmiyaBot):
        super().__init__(bot)
        self.bot = bot

    @waiting_event
    def reply_group_message(self, data: Message):
        if data.is_only_call:
            return random_reply(data, self.bot)

        if data.is_call:
            ark_result = self.arknights.find_results(data)
            if ark_result:
                return ark_result

            for func in self.functions:
                if func.check(data):
                    return func.action(data)

            for action in self.actions:
                result = action(data)
                if result:
                    return result

        return greeting(data)

    @waiting_event
    def reply_private_message(self, data: Message):
        message = data.text
        reply = Chain(data)

        if '关闭报错推送' in message:
            self.bot.send_err = False
            return reply.text('已关闭报错推送')

        if '强制更新' in message:
            self.bot.send_to_admin('开始强制更新...')
            self.arknights.download_bot_resource(refresh=True)
            self.arknights.get_ignore(reset=True)
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

                if word_in_sentence(message, ['禁用', '启用']):
                    status = int('启用' in message)
                    Admin.update(active=status).where(Admin.user_id == user_id).execute()
                    return reply.text(f'{"启用" if status else "禁用"}管理员【{user_id}】')

    @staticmethod
    def message_filter(data: Message):
        if data.is_admin is False and data.type == 'friend':
            return False

        if data.group_id and config.account.group.groupId and config.account.group.closeBeta:
            if str(data.group_id) != str(config.account.group.groupId):
                return False

        for item in ['Q群管家', '小冰']:
            if item in data.text:
                return False

        if data.is_black:
            return False

        speed = MessageBase.select().where(
            MessageBase.user_id == data.user_id,
            MessageBase.record == 'call',
            MessageBase.msg_time >= time.time() - limit.seconds
        )
        if speed.count() >= limit.maxCount:
            return Chain(data).dont_at().text('博士说话太快了，请慢一些吧～')

        return manager_handler(data) if data.type == 'group' else True
