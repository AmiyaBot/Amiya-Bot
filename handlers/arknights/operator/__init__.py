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
    def __init__(self, data_source):
        super().__init__(function_id='checkOperator')

        self.operator_module = OperatorModules(data_source)
        self.material_costs = MaterialCosts(data_source)
        self.operator_info = OperatorInfo(data_source)

        self.keywords = ['模组', '资料', '信息']
        self.keywords_pinyin = [text_to_pinyin(item) for item in self.keywords + ['材料']]

        jieba.load_userdict('resource/operators.txt')
        jieba.load_userdict('resource/stories.txt')
        jieba.load_userdict('resource/skins.txt')

    @FuncInterface.is_disable
    def check(self, data: Message):
        keyword = []
        keyword += InitData.voices
        keyword += InitData.skins
        keyword += self.material_costs.keywords
        keyword += self.operator_info.skins_keywords
        keyword += self.keywords

        for item in self.__words_list(data):
            if item in keyword:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):
        message = data.text_digits
        skin_word = word_in_sentence(message, InitData.skins)

        words = self.__words_list(data)
        info = self.__search_info(words, {
            'name': [self.material_costs.operator_map, self.material_costs.operator_list],
            'level': [self.material_costs.skill_level_list],
            'skill': [self.material_costs.skill_map],
            'skill_index': [self.material_costs.skill_index_list],
            'skin_key': [self.operator_info.skins_keywords],
            'voice_key': [InitData.voices],
            'story_key': [self.operator_info.stories_title]
        })
        info_sup = self.__search_info(data.cut_words(data.text_pinyin), {
            'name': [self.material_costs.operator_map, self.material_costs.operator_list],
            'skill': [self.material_costs.skill_map]
        })

        result = None
        reply = Chain(data)

        if info.skin_key:
            pass

        # 如果技能名不属于干员，则删除技能名，
        if self.__skill_match(info) is False:
            info.skill = ''

        # 没有查找到名字和技能时，将名字改为自己或替换到模糊搜索里的名字
        if not info.name and not info.skill:
            if info_sup.name:
                info.name = info_sup.name
            else:
                info.name = '阿米娅'

        # 没有查找到名字和技能时，如果模糊搜索里有技能名且技能和干员匹配，则使用模糊搜索
        if not info.name and not info.skill and self.__skill_match(info_sup):
            info.skill = info_sup.skill

        # 没有查找到技能等级但有技能信息时，修改到默认等级
        if info.name and (info.skill_index or info.skill) and not info.level:
            info.level = 8 if '材料' in message else 7

        if info.level != 0:
            if info.level < 0:
                info.level = abs(info.level)
                result = self.material_costs.check_evolve_costs(info)
            else:
                if info.level <= 7 and '材料' in message:
                    return reply.text('博士，暂时只可以查询专一以上的材料哦')

                elif info.level >= 8 and '材料' in message:
                    info.level -= 7
                    result = self.material_costs.check_mastery_costs(info)

                else:
                    result = self.operator_info.get_skill_data(info)

        if info.name and result is None:
            # 档案
            if info.story_key:
                result = self.operator_info.get_story(info)

            # 语音
            elif info.voice_key:
                result = self.operator_info.get_voice(info)

            # 皮肤
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

            # 模组
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

    def __skill_match(self, info: InfoInterface):
        if not info.name:
            return True
        if info.skill:
            return self.operator_info.skill_operator[info.skill] == info.name
        return False

    @staticmethod
    def __words_list(data: Message):
        return data.text_cut + data.text_cut_pinyin

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
                                res, rate = find_similar_string(item, source.keys(), hard=0.8, return_rate=True)
                                if res:
                                    setattr(info, name, source[res])
                                    raise LoopBreak(index, name)

                            elif item in source:
                                value = source[item] if type(source) is dict else item
                                if value == '阿米娅':
                                    continue
                                setattr(info, name, value)
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
