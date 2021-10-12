import re

from core import Message, Chain
from core.util.config import func_setting
from core.database.models import Disable
from core.util.common import word_in_sentence
from handlers.constraint import FuncInterface

from .function import Function


class Menu(FuncInterface):
    def __init__(self):
        super().__init__(function_id='functionQuery')

    def verify(self, data: Message):
        for item in Function.query_key + Function.source_code_key + Function.function_titles:
            if item in data.text:
                return True

    @FuncInterface.is_used
    def action(self, data: Message):
        if word_in_sentence(data.text_digits, ['关闭清单', '关闭列表']):
            text = self.check_disable(data)
        else:
            text = self.func_list(data)

        return Chain(data).text(text)

    @staticmethod
    def func_list(data: Message):

        function_list = Function.function_list

        disable = Disable.select().where(Disable.group_id == data.group_id, Disable.status == 1)
        dis_list = [item.function_id for item in disable]

        message = data.text_digits
        index = -1

        for item in Function.source_code_key:
            if item in message:
                return Function.source_code

        for item in Function.index_reg:
            r = re.search(re.compile(item), message)
            if r:
                index = int(r.group(1))

        for item in Function.function_titles:
            if item in message:
                index = Function.function_titles.index(item) + 1

        if 0 < index <= len(function_list):
            index -= 1
            text = '【%s】' % function_list[index]['title']

            status = 0
            if word_in_sentence(message, ['关闭', '禁用']):
                status = 1
            if word_in_sentence(message, ['打开', '开启']):
                status = 2

            if status and data.is_group_admin:
                func = function_list[index]
                if func['id']:
                    group = Function.function_groups[func['id']]

                    if status == 1:
                        Disable.create(
                            group_id=data.group_id,
                            function_id=func['id'],
                            status=int(status == 1)
                        )
                    else:
                        Disable.delete().where(Disable.group_id == data.group_id).execute()

                    text = f'已在本群【{data.group_id}】%s以下功能：\n\n' % ('关闭' if status == 1 else '打开')
                    text += '\n'.join([('  --  ' + n) for n in group])

                    return text
                else:
                    return '【%s】功能不可操作' % func['title']

            if function_list[index]['desc'] == 'source_code':
                return Function.source_code

            for sub_item in function_list[index]['desc']:
                text += '\n%s' % sub_item

            return text

        text = '博士，这是阿米娅的功能清单\n\n'
        text += '注意：使用阿米娅功能的时候，请务必在句子头部带上【阿米娅的名字或昵称】！\n'
        indent = [0, 0]

        setting = func_setting().globalState
        for f_id, state in setting.items():
            if not state:
                indent[0] = 5
                break

        if dis_list:
            text += f'\n注意：本群【{data.group_id}】启用了功能关闭，被关闭的功能将在下面标注\n'
            indent[1] = 5

        for index, item in enumerate(function_list):
            disabled = '【已禁用】' if item['id'] in setting and not setting[item['id']] else '　' * indent[0]
            close = '【已关闭】' if item['id'] in dis_list else '　' * indent[1]
            text += '\n%s%s[%d] %s' % (disabled, close, index + 1, item['title'])

        text += '\n\n查看功能详情，请发送「阿米娅查看第 N 个功能」或「阿米娅查看【功能名】」来获取使用方法'
        text += '\n关闭功能，请管理员发送「阿米娅关闭第 N 个功能」或「阿米娅关闭【功能名】」'

        return text

    @staticmethod
    def check_disable(data):
        disable = Disable.select().where(Disable.group_id == data.group_id)
        dis_list = [item.function_id for item in disable]

        text = f'本群【{data.group_id}】没有关闭任何功能'

        if dis_list:
            text = f'已在本群【{data.group_id}】关闭以下功能：\n'
            for item in Function.function_list:
                if item['id'] in dis_list:
                    text += '\n -- ' + item['title']

        return text
