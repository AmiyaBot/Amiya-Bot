import jieba
import copy
import re
import os

from modules.commonMethods import Reply, word_in_sentence, remove_punctuation
from message.messageType import Image
from database.baseController import BaseController
from functions.operator.materialsCosts import MaterialCosts
from functions.operator.operatorInfo import OperatorInfo
from functions.operator.initData import InitData

print('loading operators data...')
database = BaseController()
operator = OperatorInfo()
material_costs = MaterialCosts()
jieba.load_userdict('resource/operators.txt')
jieba.load_userdict('resource/stories.txt')
jieba.load_userdict('resource/skins.txt')


class LoopBreak(Exception):
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value

    def __str__(self):
        return '%s = %s' % (self.name, self.value)


class Init:
    def __init__(self):
        self.function_id = 'checkOperator'
        self.keyword = InitData.voices + material_costs.keywords + operator.skins_keywords
        self.stories_title = list(operator.stories_title.keys()) + [i for k, i in operator.stories_title.items()]

    def action(self, data):

        message = data['text_digits']
        message_ori = remove_punctuation(data['text'])

        words = jieba.lcut(
            message.lower().replace(' ', '')
        )
        words += jieba.lcut(
            message_ori.lower().replace(' ', '')
        )
        words = sorted(words, reverse=True, key=lambda i: len(i))

        operator_id = None
        info = {
            'name': '',
            'level': 0,
            'skill': '',
            'skin_key': '',
            'voice_key': '',
            'skill_index': 0,
            'stories_key': ''
        }
        info_source = {
            'name': [material_costs.operator_map, material_costs.operator_list],
            'level': [material_costs.level_list],
            'skill': [material_costs.skill_map],
            'skill_index': [material_costs.skill_index_list],
            'skin_key': [operator.skins_keywords],
            'voice_key': [InitData.voices],
            'stories_key': [self.stories_title]
        }
        info_key = list(info.keys())

        for item in words:
            try:
                # 遍历 info_key 在资源 info_source 里逐个寻找关键词
                for name in copy.deepcopy(info_key):
                    for source in info_source[name]:

                        # info_source 有两种类型（列表或字典）
                        if item in source:
                            if type(source) is dict:
                                info[name] = source[item]
                            if type(source) is list:
                                info[name] = item

                            if name == 'name':
                                operator_id = database.operator.get_operator_id(operator_name=info[name])

                            # 找到关键词后删除这个 key，后续不再匹配这个 key 的内容
                            info_key.remove(name)

                            raise LoopBreak(name=name, value=info[name])
            except LoopBreak as value:
                # print(value)
                continue

        # todo 皮肤资料
        if info['skin_key']:
            return self.find_skin(info['skin_key'])

        if info['name'] == '' and info['skill'] == '':
            return Reply('博士，想查询哪位干员的资料呢？')

        if info['level'] != 0:
            if info['level'] < 0:
                # todo 精英化资料
                info['level'] = abs(info['level'])
                result = material_costs.check_evolve_costs(info['name'], info['level'])
            else:
                if info['level'] >= 8 and '材料' in message:
                    # todo 专精资料
                    info['level'] -= 7
                    result = material_costs.check_mastery_costs(info['name'], info['skill'], info['level'],
                                                                skill_index=info['skill_index'])
                else:
                    # todo 技能数据
                    result = operator.get_skill_data(info['name'], info['skill'], info['level'],
                                                     skill_index=info['skill_index'])
            return Reply(result)

        if info['name']:
            # todo 档案资料
            if info['stories_key']:
                story = database.operator.find_operator_stories(info['name'], info['stories_key'])
                if story:
                    text = '博士，这是干员%s的《%s》档案\n\n' % (info['name'], info['stories_key'])
                    return Reply(text + story['story_text'])
                else:
                    return Reply('博士，没有找到干员%s的《%s》档案' % (info['name'], info['stories_key']))

            # todo 语音资料
            if info['voice_key']:
                return self.find_voice(info['name'], info['voice_key'])

            # todo 皮肤列表
            if word_in_sentence(message, ['皮肤', '服装']):
                if operator_id not in operator.skins_table:
                    amiya_id = database.operator.get_operator_id(operator_name='阿米娅')
                    no_skin = '博士，干员%s暂时还没有皮肤哦～（兔兔都有%d个皮肤了 ^.^）' % (info['name'], len(operator.skins_table[amiya_id]))
                    return Reply(no_skin)

                skin_list = operator.skins_table[operator_id]

                r = re.search(re.compile(r'第(\d+)个皮肤'), message)
                if r:
                    index = abs(int(r.group(1))) - 1
                    if index >= len(skin_list):
                        index = len(skin_list) - 1

                    return self.find_skin(skin_list[index]['skin_name'])
                else:
                    text = '博士，为您找到干员%s的皮肤列表\n\n' % info['name']

                    for index, item in enumerate(skin_list):
                        idx = ('' if index + 1 >= 10 else '0') + str(index + 1)
                        text += '%s [ %s - %s ] %s\n' % (idx, item['skin_group'], item['skin_name'], item['skin_usage'])

                    text += '\n请和阿米娅说「阿米娅查看%s第 N 个皮肤」查看详情吧' % info['name']

                    return Reply(text)

            if word_in_sentence(message, ['精英', '专精']):
                return Reply('博士，要告诉阿米娅精英或专精等级哦')

            if word_in_sentence(message, ['语音']):
                return Reply('博士，要告诉阿米娅语音的详细标题哦')

            if info['skill'] or info['skill_index']:
                return Reply('博士，要查询干员技能资料的话，请加上【技能等级】或者加上【技能等级和“材料”关键字】哦')

            return Reply(operator.get_detail_info(info['name']))

    @staticmethod
    def find_voice(name, voice):
        result = database.operator.find_operator_voice(name, voice)
        if result:
            text = '博士，为您找到干员%s的语音档案：\n\n【%s】\n%s' % (name, voice, result['voice_text'])
            return Reply(text)
        return Reply('抱歉博士，没有找到干员%s%s相关的语音档案' % (name, voice))

    @staticmethod
    def find_skin(skin_name):
        skin = database.operator.find_operator_skin(skin_name)
        if skin:
            opt = database.operator.get_operator_by_id(skin['operator_id'])

            text = '博士，为您找到干员%s的皮肤档案：\n\n【%s - %s】\n\n' % (opt['operator_name'], skin['skin_group'], skin['skin_name'])
            text += skin['skin_source'] + '\n\n'
            text += skin['skin_usage'] + '\n'
            text += skin['skin_content'] + '\n\n'
            text += ' -- ' + skin['skin_desc']

            reply = [Reply(text)]

            pic = 'resource/images/picture/%s.png' % skin['skin_image']
            if os.path.exists(pic):
                reply.append(Image(pic))

            return reply
