import jieba

from modules.commonMethods import Reply, find_similar_string
from functions.material.materials import Material

print('loading materials data...')
material = Material()
jieba.load_userdict('resource/materials.txt')


class Init:
    def __init__(self):
        self.function_id = 'checkMaterial'
        self.keyword = material.material_list + ['材料']

    @staticmethod
    def action(data):
        msg_words = sorted(
            jieba.lcut_for_search(data['text']),
            reverse=True,
            key=lambda i: len(i)
        )

        name = ''
        rate = 0
        for item in msg_words:
            n, r = find_similar_string(item, material.material_list, return_rate=True)
            if rate < r:
                name = n
                rate = r

        if name:
            result = material.check_material(name)
            return Reply(result)
