import re

from modules.commonMethods import Reply

from .vblog import VBlog

blog = VBlog()


class Init:
    def __init__(self):
        self.function_id = 'vblog'
        self.keyword = ['新公告', '新动态', '新消息', '微博']

    @staticmethod
    def action(data):

        message = data['text_digits']

        r = re.search(re.compile(r'第(\d+)条微博'), message)
        if r:
            index = abs(int(r.group(1)))
            result = blog.get_new_blog(message_type=data['type'], index=index - 1)
            if result:
                return result
            else:
                return Reply('博士…暂时无法获取微博呢…请稍后再试吧')

        return blog.get_blog_list()
