import re
import copy
import jieba

from core import Message, Chain
from core.util.common import find_similar_string, word_in_sentence, text_to_pinyin
from handlers.funcInterface import FuncInterface

from .operatorModules import OperatorModules
from .materialCosts import MaterialCosts
from .operatorInfo import OperatorInfo
from .initData import InfoInterface, InitData


class LoopBreak(Exception):
    def __init__(self, index, name=''):
        self.index = index
        self.name = name

    def __str__(self):
        return self.index, self.name


class Operator(FuncInterface):
    def __init__(self, game_data):
        super().__init__(function_id='checkOperator')

        self.operator_module = OperatorModules(game_data)
        self.material_costs = MaterialCosts(game_data)
        self.operator_info = OperatorInfo(game_data)

        self.keywords = ['模组', '资料', '信息']
        self.keywords_pinyin = [text_to_pinyin(item) for item in self.keywords + ['材料']]

        jieba.load_userdict('resource/operators.txt')
        jieba.load_userdict('resource/stories.txt')
        jieba.load_userdict('resource/skins.txt')

    def __cut_words(self, text) -> list:
        text = text.lower().replace(' ', '')
        for item in self.keywords + self.keywords_pinyin + ['材料']:
            text = text.replace(item, '')
        return jieba.lcut(text)

    @staticmethod
    def __search_info(words, info_source):
        info = InfoInterface()
        info_key = list(info_source.keys())

        while True:
            try:
                if len(words) == 0:
                    break
                for index, item in enumerate(words):
                    for name in copy.deepcopy(info_key):
                        for source in info_source[name]:

                            if name == 'skill':
                                res = find_similar_string(item, source.keys(), hard=0.8)
                                if res:
                                    setattr(info, name, source[res])
                                    raise LoopBreak(index, name)

                            elif item in source:
                                if type(source) is dict:
                                    setattr(info, name, source[item])
                                if type(source) is list:
                                    setattr(info, name, item)
                                raise LoopBreak(index, name)

                    if index == len(words) - 1:
                        raise LoopBreak('done')
            except LoopBreak as e:
                if e.index == 'done':
                    break
                words.pop(e.index)
                info_key.remove(e.name)
                continue

        return info

    @FuncInterface.is_disable
    def check(self, data: Message):
        words = self.__cut_words(data.text_digits)
        keyword = []
        keyword += InitData.voices
        keyword += InitData.skins
        keyword += self.material_costs.keywords
        keyword += self.operator_info.skins_keywords
        keyword += self.keywords

        for item in words:
            if item in keyword:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):
        message = data.text_digits

        words = self.__cut_words(message) + self.__cut_words(data.text)
        words = sorted(words, reverse=True, key=lambda i: len(i)) + self.__cut_words(data.text_pinyin)
        skin_word = word_in_sentence(message, InitData.skins)

        info_source = {
            'name': [self.material_costs.operator_map, self.material_costs.operator_list],
            'level': [self.material_costs.skill_level_list],
            'skill': [self.material_costs.skill_map],
            'skill_index': [self.material_costs.skill_index_list],
            'skin_key': [self.operator_info.skins_keywords],
            'voice_key': [InitData.voices],
            'story_key': [self.operator_info.stories_title]
        }
        info = self.__search_info(words, info_source)

        result = None
        reply = Chain(data)

        if info.skin_key:
            pass

        if not info.name and not info.skill:
            info.name = '阿米娅'

        # if info.name and (info.skill_index or info.skill) and not info.level:
        #     info.level = 7

        if info.level != 0:
            if info.level < 0:
                info.level = abs(info.level)
                result = self.material_costs.check_evolve_costs(info)
            else:
                if info.level >= 8 and '材料' in message:
                    info.level -= 7
                    result = self.material_costs.check_mastery_costs(info)
                else:
                    result = self.operator_info.get_skill_data(info)

        if info.name and result is None:
            if info.story_key:
                result = self.operator_info.get_story(info)

            elif info.voice_key:
                result = self.operator_info.get_voice(info)

            elif skin_word:
                r = re.search(re.compile(rf'第(\d+)个{skin_word}'), message)
                if r:
                    skin_list = self.operator_info.skins_table[info.name]
                    index = abs(int(r.group(1))) - 1

                    if index >= len(skin_list):
                        index = len(skin_list) - 1

                    result, pic = self.operator_info.build_skin_content(info, skin_list[index])
                    if pic:
                        reply.image(pic)
                else:
                    result = self.operator_info.get_skins(info)

            elif word_in_sentence(message, ['模组']):
                result = self.operator_module.find_operator_module(info)

            elif word_in_sentence(message, ['精英', '专精']):
                result = '博士，要告诉阿米娅精英或专精等级哦'

            elif word_in_sentence(message, ['语音']):
                result = '博士，要告诉阿米娅语音的详细标题哦'

            else:
                if info.name == '阿米娅' and not word_in_sentence(message, ['资料', '信息']):
                    return False
                result = self.operator_info.get_detail_info(info)

        if result:
            if type(result) is tuple:
                return reply.text_image(*result)
            else:
                return reply.text(result)
