import os
import re
import copy
import jieba

from core import Message, Chain, AmiyaBot
from core.util.common import find_similar_list, word_in_sentence
from dataSource import DataSource
from handlers.constraint import FuncInterface

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
    def __init__(self, data_source: DataSource, bot: AmiyaBot):
        super().__init__(function_id='checkOperator')

        self.operator_module = OperatorModules(data_source)
        self.material_costs = MaterialCosts(data_source)
        self.operator_info = OperatorInfo(data_source)
        self.data_source = data_source
        self.bot = bot

        self.keywords = self.keyword_list()

        for item in InitData.ignore_keywords:
            jieba.del_word(item)

        jieba.load_userdict('resource/operators.txt')
        jieba.load_userdict('resource/stories.txt')
        jieba.load_userdict('resource/skins.txt')

    def keyword_list(self):
        keyword = []
        keyword += InitData.skill_index_list.keys()
        keyword += InitData.skill_level_list.keys()
        keyword += InitData.keyword
        keyword += InitData.voices
        keyword += InitData.skins
        keyword += self.material_costs.keywords
        keyword += self.operator_info.skins_keywords

        return keyword

    @FuncInterface.is_disable
    def verify(self, data: Message):

        words = self.__words_list(data)
        hit = 0

        for item in words:
            if item in self.keywords:
                hit += 1

        return hit

    @FuncInterface.is_used
    def action(self, data: Message):
        message = data.text_digits
        skin_word = word_in_sentence(message, InitData.skins)

        info = self.__search_info(self.__words_list(data), {
            'name': [self.material_costs.operator_map, self.material_costs.operator_list],
            'level': [InitData.skill_level_list],
            'skill': [self.material_costs.skill_map],
            'skill_index': [InitData.skill_index_list],
            'skin_key': [self.operator_info.skins_keywords],
            'voice_key': [InitData.voices],
            'story_key': [self.operator_info.stories_title]
        })

        result = None
        reply = Chain(data)

        # 如果技能名不属于干员，则删除技能名，
        if self.__skill_match(info) is False:
            info.skill = ''

        # 查询立绘
        if info.name and (info.skin_key or skin_word) and not (not skin_word and info.skin_key in ['精英一', '精英二']):
            skin_item = None
            r = re.search(re.compile(rf'第(\d+)个{skin_word}'), message)
            if r:
                skin_list = self.operator_info.skins_table[info.name]
                index = abs(int(r.group(1))) - 1

                if index >= len(skin_list):
                    index = len(skin_list) - 1

                skin_item = skin_list[index]
            else:
                skin_map = self.operator_info.get_skins(info)
                if info.skin_key and info.skin_key in skin_map[1]:
                    skin_item = skin_map[1][info.skin_key]
                else:
                    result = skin_map[0]

            if skin_item:
                result, pic = self.operator_info.build_skin_content(info, skin_item)
                if not os.path.exists(pic):
                    self.bot.send_message(Chain(data, quote=False).text('正在下载立绘，博士请稍等...'))
                    res = self.data_source.get_pic(skin_item['skin_id'], 'skins', 'cloud', False)
                    if res:
                        reply.image(pic).text('\n')
                    else:
                        result += '\n\n立绘下载失败...>.<'
                else:
                    reply.image(pic).text('\n')

        if info.level != 0 and result is None:
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

            # 语音
            if info.voice_key:
                result, exists = self.operator_info.get_voice(info)
                result = result.replace('{@nickname}', data.nickname)
                if exists:
                    wiki_name = self.data_source.operators[info.name].wiki_name
                    file = self.data_source.wiki.voice_exists(wiki_name, info.voice_key)
                    if not file:
                        self.bot.send_message(Chain(data, quote=False).text('正在下载语音文件，博士请稍等...'))
                        file = self.data_source.wiki.download_operator_voices(wiki_name, info.voice_key)
                        if not file:
                            self.bot.send_message(Chain(data).text('语音文件下载失败...>.<'))
                    if file:
                        reply.voice(file)

            # 模组
            elif word_in_sentence(message, ['模组']):
                result = self.operator_module.find_operator_module(info, '故事' in message)

            elif word_in_sentence(message, ['档案', '资料']) or info.story_key:
                result = self.operator_info.get_story(info, not info.story_key)

            elif word_in_sentence(message, ['精英', '专精']):
                result = '博士，要告诉阿米娅精英或专精等级哦'

            elif word_in_sentence(message, ['语音']):
                result = '博士，要告诉阿米娅语音的详细标题哦'

            else:
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
        return data.text_cut

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
                                res, rate = find_similar_list(item, source.keys(), _random=True)
                                if res:
                                    setattr(info, name, source[res])
                                    raise LoopBreak(index, name)

                            elif item in source:
                                value = source[item] if type(source) is dict else item

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
