import jieba

from jieba import posseg
from modules.commonMethods import Reply, find_similar_string
from functions.material.materials import Material

print('loading materials data...')
material = Material()
jieba.load_userdict('resource/materials.txt')


class Init:
    def __init__(self):
        self.function_id = 'checkMaterial'
        self.keyword = material.material_list

    @staticmethod
    def action(data):
        msg_words = posseg.lcut(data['text'])

        name = ''
        rate = 0
        for item in [n.word for n in msg_words]:
            n, r = find_similar_string(item, material.material_list, return_rate=True)
            if rate < r:
                name = n
                rate = r

        if name:
            result = material.check_material(name)
            return Reply(result)
