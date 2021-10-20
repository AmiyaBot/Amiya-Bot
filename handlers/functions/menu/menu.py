from core import Message, Chain
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
                return 10

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

        message = data.text_digits
        index = -1

        for item in Function.source_code_key:
            if item in message:
                return Function.source_code

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

            return text

        text = '博士，这是阿米娅的功能指引\nhttps://vivien8261.gitee.io/amiya-bot/?file=function'

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
