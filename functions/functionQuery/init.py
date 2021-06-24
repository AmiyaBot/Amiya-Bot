import re

from message.messageType import TextImage
from modules.commonMethods import Reply, word_in_sentence
from functions.functionQuery.function import Function
from database.baseController import BaseController

function_list = Function.function_list
database = BaseController()


class Init:
    def __init__(self):
        self.function_id = 'functionQuery'
        self.keyword = Function.query_key + Function.source_code_key + Function.function_titles

    def action(self, data):
        if word_in_sentence(data['text_digits'], ['关闭清单', '关闭列表']):
            text = self.disable_func(data)
        else:
            text = self.func_list(data)

        return Reply(TextImage(text))

    @staticmethod
    def func_list(data):
        disable = database.function.get_disable_function(data['group_id'])
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
        if disable:
            text += '\n注意：本群【%s】启用了功能关闭，被关闭的功能将在下面标注\n' % data['group_id']
        for index, item in enumerate(function_list):
            text += '\n%s[%d] %s' % ('【已关闭】' if item['id'] in disable else '　' * 5, index + 1, item['title'])

        text += '\n\n查看功能详情，请发送「阿米娅查看第 N 个功能」或「阿米娅查看【功能名】」来获取使用方法'
        text += '\n要关闭单个功能，请管理员发送「阿米娅关闭第 N 个功能」'

        return text

    @staticmethod
    def disable_func(data):
        disable = database.function.get_disable_function(data['group_id'])
        text = ''
        if disable:
            text += '已在本群【%s】关闭以下功能：\n' % data['group_id']
            for item in function_list:
                if item['id'] in disable:
                    text += '\n -- ' + item['title']
        return text
