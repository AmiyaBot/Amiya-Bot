import re

from message.messageType import TextImage
from modules.commonMethods import Reply
from functions.functionQuery.function import Function

function_list = Function.function_list


class Init:
    def __init__(self):
        self.function_id = 'functionQuery'
        self.keyword = Function.query_key + Function.source_code_key + Function.function_titles

    @staticmethod
    def action(data):

        message = data['text_digits']
        index = -1

        for item in Function.source_code_key:
            if item in message:
                return Reply(Function.source_code)

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

            if function_list[index]['desc'] == 'source_code':
                return Reply(Function.source_code)

            for sub_item in function_list[index]['desc']:
                text += '\n%s' % sub_item

            return Reply(TextImage(text))

        text = '博士，这是阿米娅的功能清单\n\n'
        text += '温馨提醒：使用阿米娅功能的时候，请务必在句子头部带上【阿米娅的名字或昵称】！\n'
        for index, item in enumerate(function_list):
            text += '\n[%d] %s' % (index + 1, item['title'])

        text += '\n\n查看功能详情，请发送「阿米娅查看第 N 个功能」或「阿米娅查看【功能名】」来获取使用方法'
        text += '\n要关闭单个功能，请管理员发送「阿米娅关闭第 N 个功能」'

        return Reply(TextImage(text))
