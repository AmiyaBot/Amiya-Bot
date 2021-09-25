import os
import re

from core.util import log
from core.util.imageCreator import TextParser, line_height, side_padding
from core.util.numberTranslate import chinese_to_digits
from core.util.common import word_in_sentence, integer
from dataSource import DataSource, Operator
from dataSource.builder import attr_dict

from .initData import InfoInterface, InitData

skill_images_source = 'resource/images/skills/'
avatars_images_source = 'resource/images/avatars/'

icon_size = 36


class OperatorInfo:
    def __init__(self, data: DataSource):
        self.data = data
        self.stories_title = {}
        self.skins_table = {}
        self.skins_keywords = []
        self.skill_operator = {}

        self.init_skill_operator()
        self.init_stories_titles()
        self.init_skins_table()

    def init_skill_operator(self):
        for name, item in self.data.operators.items():
            skills = item.skills()[0]
            for skl in skills:
                self.skill_operator[skl['skill_name']] = name

    def init_stories_titles(self):
        log.info('building operator\'s stories keywords dict...')
        stories_title = {}
        stories_keyword = []

        for name, item in self.data.operators.items():
            stories = item.stories()
            stories_title.update(
                {chinese_to_digits(item['story_title']): item['story_title'] for item in stories}
            )

        for index, item in stories_title.items():
            item = re.compile(r'？+', re.S).sub('', item)
            if item:
                stories_keyword.append(item + ' 500 n')

        self.stories_title = list(stories_title.keys()) + [i for k, i in stories_title.items()]

        with open('resource/stories.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join(stories_keyword))

    def init_skins_table(self):
        log.info('building operator\'s skins keywords dict...')
        skins_table = {}
        skins_keywords = [] + InitData.skins

        for name, item in self.data.operators.items():
            skins = item.skins()
            skins_table[item.name] = skins
            skins_keywords += [n['skin_name'] for n in skins]

        self.skins_table = skins_table
        self.skins_keywords = skins_keywords

        with open('resource/skins.txt', mode='w', encoding='utf-8') as file:
            file.write('\n'.join([n + ' 500 n' for n in skins_keywords]))

    def get_story(self, info: InfoInterface):
        operator: Operator = self.data.operators[info.name]

        stories = operator.stories()
        for item in stories:
            if item['story_title'] == info.story_key:
                return f'博士，这是干员{info.name}《{info.story_key}》的档案\n\n{item["story_text"]}'
            else:
                return f'博士，没有找到干员{info.name}《{info.story_key}》的档案'

    def get_voice(self, info: InfoInterface):
        operator: Operator = self.data.operators[info.name]

        voices = operator.voices()
        for item in voices:
            if item['voice_title'] == info.voice_key:
                return f'博士，为您找到干员{info.name}的语音档案：\n\n【{info.voice_key}】\n\n{item["voice_text"]}', True

        return f'博士，没有找到干员{info.name}{info.voice_key}相关的语音档案', False

    def get_skins(self, info: InfoInterface):
        skins = self.skins_table[info.name]
        skins_map = {}

        if not skins:
            return f'博士，干员{info.name}暂时还没有立绘哦～', skins_map

        text = f'博士，为您找到干员{info.name}的立绘列表\n\n'

        for index, item in enumerate(skins):
            text += f'{index + 1} [ {item["skin_name"]} ] {item["skin_usage"]}\n'
            skins_map[item['skin_name']] = item

        text += f'\n请和阿米娅说「阿米娅查看{info.name}第 N 个立绘」查看详情吧'

        return text, skins_map

    def get_detail_info(self, info: InfoInterface):
        operator: Operator = self.data.operators[info.name]

        detail, trust = operator.detail()
        talents = operator.talents()
        potential = operator.potential()
        building_skills = operator.building_skills()

        text = '博士，为您找到以下干员资料\n\n\n\n\n\n\n'
        icons = [
            {
                'path': avatars_images_source + operator.id + '.png',
                'size': (80, 80),
                'pos': (side_padding, 30)
            }
        ]

        text += '%s [%s]\n%s\n\n' % (operator.name,
                                     operator.en_name,
                                     '★' * operator.rarity)

        text += '%s\n' % operator.range

        text += '【职业】%s - %s\n　%s\n\n' % (operator.classes, operator.classes_sub, detail['operator_trait'])
        text += '%s\n -- 「%s」\n\n' % (detail['operator_usage'], detail['operator_quote'])

        text += '【信物】\n　%s\n\n' % detail['operator_token'] if detail['operator_token'] else ''

        text += '【精英 %s 级属性】\n' % detail['max_level']

        for key, name in attr_dict.items():
            text += f' -- {name}：'
            if key in detail:
                text += str(integer(detail[key]))
            if key in trust and int(trust[key]):
                text += '(%s)' % integer(trust[key])
            text += '\n'

        talents_text = ''
        for item in talents:
            talents_text += '<[%s@#174CC6]>\n　%s\n' % (item['talents_name'], item['talents_desc'])
        text += ('\n【天赋】\n%s\n' % talents_text) if talents_text else ''

        potential_text = ''
        for item in potential:
            potential_text += '　[%s] %s\n' % (InitData.potential_rank[item['potential_rank']], item['potential_desc'])
        text += ('【潜能】\n%s\n' % potential_text) if potential_text else ''

        building_text = ''
        for item in building_skills:
            building_text += '<[%s@#174CC6]>\n　[精英%s解锁@#D60008]\n　%s\n' % \
                             (item['bs_name'], item['bs_unlocked'], item['bs_desc'])
        text += ('【基建技能】\n%s\n' % building_text) if building_text else ''

        info.level = 7
        info.skill = ''
        info.skill_index = 0
        skill_list, skills_cost, skills_desc = self.check_skill_list(
            self.skill_operator,
            self.data.operators,
            info
        )

        result = []

        for skl in skill_list:
            details = skills_desc[skl['skill_no']]
            dt = {
                'skill_name': skl['skill_name'],
                'skill_index': skl['skill_index'],
                'skill_icon': skl['skill_icon']
            }
            dt.update(details[info.level - 1])
            result.append(dt)

        if result:
            text += '【7级技能】\n\n'
            top = TextParser(text).line * line_height + int(line_height / 2) + side_padding
            content, skill_icons = self.build_skill_content(result, top)

            text += content
            icons += skill_icons

        return text, icons

    def get_skill_data(self, info: InfoInterface):

        check_res = OperatorInfo.check_skill_list(
            self.skill_operator,
            self.data.operators,
            info
        )

        if type(check_res) is str:
            return check_res
        else:
            skill_list, skills_cost, skills_desc = check_res

        result = []

        for skl in skill_list:
            details = skills_desc[skl['skill_no']]

            if info.level > len(details):
                return f'博士，干员{info.name}的技能等级最大只能到{len(details)}级哦'

            dt = {
                'skill_name': skl['skill_name'],
                'skill_index': skl['skill_index'],
                'skill_icon': skl['skill_icon']
            }
            dt.update(details[info.level - 1])
            result.append(dt)

        if len(result):
            text = f'博士，这是干员{info.name}技能{InitData.skill_level[info.level]}的数据\n\n'

            top = side_padding + line_height + int((line_height * 3 - icon_size) / 2)
            content, icons = self.build_skill_content(result, top)

            text += content
            return text, icons
        else:
            return f'博士，没有找到干员{info.name}技能{InitData.skill_level[info.level]}的数据'

    @staticmethod
    def build_skin_content(info: InfoInterface, skin):
        text = f'博士，为您找到干员{info.name}的立绘档案：\n\n'
        text += '系列：' + skin['skin_group'] + '\n'
        text += '名称：' + skin['skin_name'] + '\n'
        text += '获得途径：' + skin['skin_source'] + '\n\n'
        text += skin['skin_usage'] + '\n'
        text += skin['skin_content'] + '\n\n'
        text += ' -- ' + skin['skin_desc']

        pic = 'resource/images/skins/%s.png' % skin['skin_id']

        return text, pic

    @staticmethod
    def build_skill_content(result, position):
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

            y += 48 if index else 0
            yl.append(y)

            for item in skills[name]:
                content += '%s\n' % item['range']
                content += '%s / %s' % (InitData.sp_type[item['sp_type']], InitData.skill_type[item['skill_type']])
                content += '%sSP：%s / %s\n' % (' ' * 5, item['sp_init'], item['sp_cost'])
                if item['duration'] > 0:
                    content += '持续时间：%ss\n' % item['duration']
                content += '%s\n\n' % item['description'].replace('\\\\n', '\n')
                text += content

                y += TextParser(content).line * line_height

        for index, item in enumerate(skill_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': (icon_size, icon_size),
                    'pos': (side_padding, yl[index])
                })

        return text, icons

    @staticmethod
    def check_skill_list(skill_operator, operators, info: InfoInterface):
        if not info.skill and not info.name:
            return '博士，请仔细描述想要查询的信息哦'

        if info.skill and word_in_sentence(info.skill, ['α', 'β', 'γ']):
            return f'博士，"{info.skill}"这类属于泛用技能名\n请用「干员一技能专三」这种方式向阿米娅描述吧'

        if not info.name:
            if info.skill in skill_operator:
                info.name = skill_operator[info.skill]
            else:
                return '博士，无法匹配到拥有这个技能的干员哦'

        operator: Operator = operators[info.name]

        skills, skills_id, skills_cost, skills_desc = operator.skills()

        skill_index = info.skill_index
        if info.skill and not info.skill_index:
            for index, item in enumerate(skills):
                if item['skill_name'] == info.skill:
                    skill_index = index + 1
                    break

        if skill_index > len(skills_id):
            return f'博士，干员{info.name}的只有{len(skills_id)}个技能哦'

        skill_list = [skills[skill_index - 1]] if skill_index else skills

        return skill_list, skills_cost, skills_desc
