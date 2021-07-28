import os
import re

from library.imageCreator import split_text
from library.numberTranslate import chinese_to_digits
from database.baseController import BaseController
from message.messageType import TextImage
from functions.operator.materialsCosts import MaterialCosts, skill_images_source
from functions.operator.initData import InitData

database = BaseController()
avatars_images_source = 'resource/images/avatars/'


class OperatorInfo:
    def __init__(self):
        self.skins_table = {}
        self.skins_keywords = []
        self.stories_title = {}

        self.init_skins_table()
        self.init_stories_titles()

    def init_skins_table(self):
        skins_data = database.operator.get_all_skins()
        skins_table = {}
        skins_keywords = []

        for item in skins_data:
            if item['operator_id'] not in skins_table:
                skins_table[item['operator_id']] = []
            skins_table[item['operator_id']].append(item)
            skins_keywords.append(item['skin_name'])

        self.skins_table = skins_table
        self.skins_keywords = skins_keywords

        with open('resource/skins.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([n + ' 100 n' for n in skins_keywords]))

    def init_stories_titles(self):
        stories_titles = database.operator.get_all_stories_title()

        self.stories_title = {chinese_to_digits(item['story_title']): item['story_title'] for item in stories_titles}

        stories_keyword = []
        for index, item in self.stories_title.items():
            item = re.compile(r'？+', re.S).sub('', item)
            if item:
                stories_keyword.append(item + ' 100 n')

        with open('resource/stories.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(stories_keyword))

    def get_detail_info(self, name):

        operator_id = database.operator.get_operator_id(operator_name=name)
        base, detail, trust, talents, potential, building_skill = database.operator.find_operator_all_detail(
            operator_id
        )

        text = '博士，为您找到以下干员资料\n\n\n\n\n\n\n'
        icons = [
            {
                'path': avatars_images_source + base['operator_avatar'] + '.png',
                'size': (80, 80),
                'pos': (10, 30)
            }
        ]

        text += '%s [%s]\n%s\n\n' % (base['operator_name'],
                                     base['operator_en_name'],
                                     '★' * base['operator_rarity'])

        text += '【%s干员】\n%s\n\n' % (InitData.class_type[base['operator_class']], detail['operator_desc'])
        text += '%s\n -- 「%s」\n\n' % (detail['operator_usage'], detail['operator_quote'])

        text += '【信物】\n%s\n\n' % detail['operator_token'] if detail['operator_token'] else ''

        text += '【精英%s级属性】\n' % detail['max_level']

        text += ' -- 生命值：%s\n' % (
            detail['max_hp'] if trust['max_hp'] == '0' else f"{detail['max_hp']}({trust['max_hp']})")
        text += ' -- 攻击力：%s\n' % (
            detail['attack'] if trust['attack'] == '0' else f"{detail['attack']}({trust['attack']})")
        text += ' -- 防御力：%s\n' % (
            detail['defense'] if trust['defense'] == '0' else f"{detail['defense']}({trust['defense']})")

        text += ' -- 魔法抗性：%s\n' % detail['magic_resistance']
        text += ' -- 费用：%s\n' % detail['cost']
        text += ' -- 阻挡数：%s\n' % detail['block_count']
        text += ' -- 基础攻击间隔：%ss\n' % detail['attack_time']
        text += ' -- 再部署时间：%ss\n\n' % detail['respawn_time']

        talents_text = ''
        for item in talents:
            talents_text += '<%s>\n%s\n' % (item['talents_name'], item['talents_desc'])
        text += ('【天赋】\n%s\n' % talents_text) if talents_text else ''

        potential_text = ''
        for item in potential:
            potential_text += '[%s] %s\n' % (InitData.potential_rank[item['potential_rank']], item['potential_desc'])
        text += ('【潜能】\n%s\n' % potential_text) if potential_text else ''

        building_text = ''
        for item in building_skill:
            building_text += '<%s>[精英%s解锁]\n%s\n' % (item['bs_name'], item['bs_unlocked'], item['bs_desc'])
        text += ('【基建技能】\n%s\n' % building_text) if building_text else ''

        result = database.operator.find_operator_skill_description(name, level=7)
        if result:
            text += '【7级技能】\n\n'
            top = len(split_text(text)) * 17 + 11

            content, skill_icons = self.load_skill_content(result, top)

            text += content
            icons += skill_icons

        return TextImage(text, icons)

    def get_skill_data(self, name, skill, level, skill_index=0):

        text, name, skill_index = MaterialCosts.find_repeat_skill_name(name, skill, skill_index)

        if text:
            return text

        result = database.operator.find_operator_skill_description(name, level, skill_index)

        if len(result):
            text += '博士，这是干员%s技能%s的数据\n\n' % (name, InitData.skill_level[level])

            content, icons = self.load_skill_content(result, 28)

            text += content
            return TextImage(text, icons)
        else:
            return '博士，没有找到干员%s技能%s的数据' % (name, InitData.skill_level[level])

    @staticmethod
    def load_skill_content(result, position):
        text = ''
        skills = {}
        skill_images = []
        icons = []

        y = position
        yl = []

        for item in result:
            skill_name = item['skill_name']
            if skill_name not in skills:
                skills[skill_name] = []
                skill_images.append(skill_images_source + item['skill_icon'] + '.png')
            skills[skill_name].append(item)

        for name in skills:
            text += '%s%s\n\n' % (' ' * 15, name)
            content = ''
            index = list(skills.keys()).index(name)

            y += 51 if index else 0
            yl.append(y)

            for item in skills[name]:
                content += '%s / %s' % (InitData.sp_type[item['sp_type']], InitData.skill_type[item['skill_type']])
                content += '%sSP：%s / %s\n' % (' ' * 5, item['sp_init'], item['sp_cost'])
                if item['duration'] > 0:
                    content += '持续时间：%ss\n' % item['duration']
                content += '%s\n\n' % item['description']
                text += content

                y += len(split_text(content)) * 17

        for index, item in enumerate(skill_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': (35, 35),
                    'pos': (10, yl[index])
                })

        return text, icons
