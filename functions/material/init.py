import jieba

from jieba import posseg

from modules.commonMethods import Reply
from .materials import Material

material = Material()
jieba.load_userdict('resource/materials.txt')


class Init:
    def __init__(self):
        self.function_id = 'checkMaterial'
        self.keyword = material.material_list

    def action(self, data):
        msg_words = posseg.lcut(data['text'])

        name = ''

        for item in msg_words:
            if name == '' and item.flag == 'n' and item.word in material.material_list:
                name = item.word

        if name == '':
            return Reply('抱歉博士，没有找到相关资料哦')

        result = material.check_material(name)

        return Reply(result)
