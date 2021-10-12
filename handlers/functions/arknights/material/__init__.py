import jieba

from core import Message, Chain
from core.util.common import find_similar_list
from handlers.constraint import FuncInterface

from .materialData import MaterialData


class Material(FuncInterface):
    def __init__(self, data_source):
        super().__init__(function_id='checkMaterial')

        self.material_data = MaterialData(data_source)

        jieba.load_userdict('resource/materials.txt')

    @FuncInterface.is_disable
    def verify(self, data: Message):
        for item in ['材料'] + self.material_data.material_list:
            if item in data.text:
                return True

    @FuncInterface.is_used
    def action(self, data: Message):
        words = sorted(
            jieba.lcut_for_search(data.text),
            reverse=True,
            key=lambda i: len(i)
        )

        name = ''
        rate = 0
        for item in words:
            n, r = find_similar_list(item, self.material_data.material_list, _random=True)
            if rate < r:
                name = n
                rate = r

        if name:
            result = self.material_data.check_material(name)
            if result:
                return Chain(data).text_image(*result)
