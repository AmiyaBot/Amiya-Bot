import re

from database.baseController import BaseController

database = BaseController()


class OperatorInfo:
    def __init__(self):
        self.stories_title = database.operator.get_all_stories_title()
        self.stories_keyword = []

        for item in self.stories_title:
            item = re.compile(r'？+', re.S).sub('', item)
            if item:
                self.stories_keyword.append(item + ' 100 n')

        with open('resource/stories.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(self.stories_keyword))
