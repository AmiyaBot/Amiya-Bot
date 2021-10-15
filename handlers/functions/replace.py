import re
import time

from core import Message, Chain, AmiyaBot
from core.util.config import config, keyword
from core.util.baiduCloud import ContentCensor
from core.database.models import ReplaceText
from handlers.constraint import FuncInterface


class Replace(FuncInterface):
    def __init__(self, bot: AmiyaBot):
        super().__init__(function_id='replaceText')

        self.bot = bot
        self.censor = ContentCensor(config.baiduCloud)

    @FuncInterface.is_disable
    def verify(self, data: Message):
        if '别名' in data.text:
            return 10

    @FuncInterface.is_used
    def action(self, data: Message):
        r = re.search(r'(\S+)别名(\S+)', data.remove_name(data.text_origin))
        if r:
            origin = r.group(1)
            target = r.group(2)

            if '查看' in data.text_origin:
                replace_list = ReplaceText.select().where(ReplaceText.group_id == data.group_id,
                                                          ReplaceText.origin == target)
                if replace_list:
                    text = f'找到 [{target}] 在本群生效的别名:\n'
                    for item in replace_list:
                        item: ReplaceText
                        text += f'{item.target}{"（审核通过）" if item.is_active else "（未审核通过）"}\n'
                    return Chain(data).text(text.strip('、'))
                else:
                    return Chain(data).text(f'没有找到 [{target}] 在本群生效的别名')

            if origin == '删除':
                ReplaceText.delete().where(ReplaceText.group_id == data.group_id,
                                           ReplaceText.target == target).execute()
                return Chain(data).text(f'已在本群删除别名 [{target}]')

            exist: ReplaceText = ReplaceText.get_or_none(group_id=data.group_id, target=target)
            if exist:
                text = f'本群别名识别已存在 [{origin}] > [{target}] '
                if exist.is_active == 0:
                    text += '（未审核通过）'
                return Chain(data).text(text)

            self.bot.send_message(Chain(data, quote=False).text('正在审核，博士请稍等...'))

            if not self.check_buitin(target) and not self.check_name(origin):
                return Chain(data).text(f'审核不通过！检测到存在破坏性规则')

            check = self.censor.text_censor(target)

            if not check or check['conclusionType'] in [3, 4]:
                ReplaceText.create(
                    user_id=data.user_id,
                    group_id=data.group_id,
                    origin=origin,
                    target=target,
                    in_time=int(time.time()),
                    is_active=0
                )
                text = ''
                if check and check['conclusionType'] == 3:
                    for item in check['data']:
                        text += item['msg'] + '\n'

                return Chain(data).text(f'审核未通过！请等待管理员确认批准\n{text}')

            if check['conclusionType'] == 2:
                text = '审核不通过！检测到以下违规内容：\n'
                for item in check['data']:
                    text += item['msg'] + '\n'

                return Chain(data).text(text)

            if check['conclusionType'] == 1:
                ReplaceText.create(
                    user_id=data.user_id,
                    group_id=data.group_id,
                    origin=origin,
                    target=target,
                    in_time=int(time.time())
                )
                return Chain(data).text(f'审核通过！别名识别 [{origin}] > [{target}] 已在本群生效')

    def check_buitin(self, text):
        files = [
            'enemies.txt',
            'materials.txt',
            'operators.txt',
            'skins.txt',
            'stories.txt',
            'tags.txt'
        ]
        if self.check_name(text):
            for file in files:
                with open(f'resource/{file}', mode='r', encoding='utf-8') as src:
                    content = src.read().strip('\n').split('\n')
                for item in content:
                    item = item.replace(' 500 n', '')
                    if item == text:
                        return False
        else:
            return False
        return True

    @staticmethod
    def check_name(text):
        for item in keyword.name.good:
            if item == text:
                return False
        return True
