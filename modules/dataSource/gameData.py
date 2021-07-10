import re

from database.baseController import BaseController
from modules.commonMethods import remove_xml_tag, TimeRecord
from modules.dataSource.builder import Operator, OperatorTags
from modules.dataSource.sourceBank import SourceBank
from modules.dataSource.updateConfig import Config

database = BaseController()


class GameData(SourceBank):
    def __init__(self, network=True):
        super().__init__(network)

    def get_recruit_operators(self):
        recruit_detail = remove_xml_tag(self.get_json_data('gacha_table')['recruitDetail'])
        recruit_group = re.findall(r'★\\n(.*)', recruit_detail)
        recruit_operators = []

        for item in recruit_group:
            recruit_operators += item.replace(' ', '').split('/')

        return recruit_operators

    def init_operators(self):
        print('初始化全干员数据...', end='')

        time_rec = TimeRecord()
        recruit_operators = self.get_recruit_operators()
        operators_data = self.get_json_data('character_table')
        voice_data = self.get_json_data('charword_table')
        skins_data = self.get_json_data('skin_table')['charSkins']

        operators = []
        voice_map = {}
        skins_map = {}

        map_data = (
            (voice_data, voice_map),
            (skins_data, skins_map)
        )

        for map_item in map_data:
            for n, item in map_item[0].items():
                char_id = item['charId']
                if char_id not in map_item[1]:
                    map_item[1][char_id] = []

                map_item[1][char_id].append(item)

        for code, item in operators_data.items():
            if item['profession'] not in Config.classes:
                continue

            operators.append(
                Operator(
                    code=code,
                    data=item,
                    voice_list=voice_map[code] if code in voice_map else [],
                    skins_list=skins_map[code] if code in skins_map else [],
                    recruit=item['name'] in recruit_operators
                )
            )

        print('耗时 %sms' % time_rec.rec(millisecond=True))
        return operators

    def init_enemies(self):
        enemies_info = self.get_json_data('enemy_handbook_table')
        enemies_data = self.get_json_data('enemy_database')['enemies']

        data = {}
        for item in enemies_data:
            if item['Key'] in enemies_info:
                info = enemies_info[item['Key']]
                data[info['name']] = {
                    'info': info,
                    'data': item['Value']
                }

        return data

    @staticmethod
    def save_operator_data(operator):
        rarity = operator.rarity
        time_rec = TimeRecord()

        # todo 保存基础信息
        database.operator.add_operator([{
            'operator_no': operator.id,
            'operator_name': operator.name,
            'operator_en_name': operator.en_name,
            'operator_rarity': rarity,
            'operator_avatar': operator.id,
            'operator_class': operator.classes_code,
            'available': 1 if rarity >= 2 and operator.name not in Config.unavailable else 0,
            'in_limit': 1 if operator.name in Config.limit else 0
        }])

        # todo 保存公招 Tags 信息
        if operator.recruit:
            operator_tags = OperatorTags(operator.name, rarity)
            operator_tags.append(operator.classes)
            operator_tags.append(operator.type)

            if str(rarity) in Config.high_star:
                operator_tags.append(Config.high_star[str(rarity)])

            for tag in operator.tags:
                operator_tags.append(tag)

            database.operator.add_operator_tags_relation(operator_tags.tags)

        # todo 保存详细资料
        operator_id = database.operator.get_operator_id(operator_no=operator.id)

        skins = operator.skins(operator_id)
        detail = operator.detail(operator_id)
        voices = operator.voices(operator_id)
        stories = operator.stories(operator_id)
        talents = operator.talents(operator_id)
        potential = operator.potential(operator_id)
        evolve_costs = operator.evolve_costs(operator_id)
        building_skills = operator.building_skills(operator_id)
        skills, skills_id, skills_cost, skills_desc = operator.skills(operator_id)

        database.operator.add_operator_detail([detail])

        if skins:
            database.operator.add_operator_skins(skins)
        if voices:
            database.operator.add_operator_voice(voices)
        if stories:
            database.operator.add_operator_stories(stories)
        if talents:
            database.operator.add_operator_talents(talents)
        if potential:
            database.operator.add_operator_potential(potential)
        if evolve_costs:
            database.operator.add_operator_evolve_costs(evolve_costs)
        if building_skills:
            database.operator.add_operator_building_skill(building_skills)
        if skills:
            database.operator.add_operator_skill(skills)

        skills_id = {no: database.operator.get_skill_id(no, operator_id) for no in skills_id}

        task_list = [
            (skills_cost, database.operator.add_operator_skill_mastery_costs),
            (skills_desc, database.operator.add_operator_skill_description)
        ]
        for task in task_list:
            save_list = []
            for sk_no, sk_list in task[0].items():
                for item in sk_list:
                    item['skill_id'] = skills_id[sk_no]
                    save_list.append(item)
            if save_list:
                task[1](save_list)

        print('耗时 %sms' % time_rec.rec(millisecond=True))

    def save_operator_photo(self, operators=None):
        if operators is None:
            operators = self.init_operators()

        print('开始下载干员图片资源...')
        avatars_count = 0
        photo_count = 0
        skills_count = 0
        skills_total = 0
        skins_count = 0
        skins_total = 0
        for operator in operators:
            print('正在下载干员 [%s] 图片资源...' % operator.name)

            print(' -- 头像...', end='')
            res = self.get_pic('char/profile/' + operator.id, 'avatars')
            avatars_count += 1 if res else 0
            print('OK' if res else 'NG')

            print(' -- 半身照...', end='')
            res = self.get_pic('char/halfPic/%s_1' % operator.id, 'photo', '?x-oss-process=style/small-test')
            photo_count += 1 if res else 0
            print('OK' if res else 'NG')

            skills_list = operator.skills(None)[0]
            skills_total += len(skills_list)
            for skill in skills_list:
                print(' -- 技能图标 [%s]...' % skill['skill_name'], end='')
                res = self.get_pic('skills/pics/' + skill['skill_icon'], 'skills')
                skills_count += 1 if res else 0
                print('OK' if res else 'NG')

            skins_list = operator.skins(None)
            skins_total += len(skins_list)
            for skin in skins_list:
                print(' -- 立绘 [%s][%s]...' % (skin['skin_group'], skin['skin_name']), end='')
                res = self.get_pic('char/set/' + skin['skin_image'], 'picture')
                skins_count += 1 if res else 0
                print('OK' if res else 'NG')

        print('干员图片资源下载完成')
        return ('%d/%d' % (avatars_count, len(operators)),
                '%d/%d' % (photo_count, len(operators)),
                '%d/%d' % (skills_count, skills_total),
                '%d/%d' % (skins_count, skins_total))

    def save_materials_data(self):
        building_data = self.get_json_data('building_data')
        item_data = self.get_json_data('item_table')
        formulas = {
            'WORKSHOP': building_data['workshopFormulas'],
            'MANUFACTURE': building_data['manufactFormulas']
        }

        materials = []
        materials_made = []
        materials_source = []
        for item_id, item in item_data['items'].items():
            if item_id.isdigit():
                material_name = item['name'].strip()
                icon_name = item['iconId']

                print('构建材料数据 [%s]...' % material_name, end='')

                materials.append({
                    'material_id': item_id,
                    'material_name': material_name,
                    'material_icon': icon_name,
                    'material_desc': item['usage']
                })
                self.get_pic('item/pic/' + icon_name, 'materials')

                for drop in item['stageDropList']:
                    materials_source.append({
                        'material_id': item_id,
                        'source_place': drop['stageId'],
                        'source_rate': drop['occPer']
                    })

                for build in item['buildingProductList']:
                    if build['roomType'] in formulas and build['formulaId'] in formulas[build['roomType']]:
                        build_cost = formulas[build['roomType']][build['formulaId']]['costs']
                        for build_item in build_cost:
                            materials_made.append({
                                'material_id': item_id,
                                'use_material_id': build_item['id'],
                                'use_number': build_item['count'],
                                'made_type': build['roomType']
                            })

                print('完成')

        print('保存全部材料数据...', end='')
        if materials:
            database.material.add_material(materials)
        if materials_made:
            database.material.add_material_made(materials_made)
        if materials_source:
            database.material.add_material_source(materials_source)

        print('完成')
        return len(materials)

    def save_stages_data(self):
        stage_data = self.get_json_data('stage_table')['stages']
        stage_list = []

        for stage_id, item in stage_data.items():
            if '#f#' not in stage_id and item['name']:
                stage_list.append({
                    'stage_id': stage_id,
                    'stage_code': item['code'],
                    'stage_name': item['name']
                })

        database.material.update_stage(stage_list)

        return len(stage_list)

    def save_enemies_photo(self):
        enemies = self.init_enemies()

        success = 0
        total = 0
        for name, item in enemies.items():
            print('正在下载敌人 [%s] 图片资源...' % name, end='')
            res = self.get_pic('enemy/pic/' + item['info']['enemyId'], 'enemy', '?x-oss-process=style/jpg-test')

            success += 1 if res else 0
            total += 1

            print('OK' if res else 'NG')

        return '%d/%d' % (success, total)

    def exec_sql_file(self):
        for item in self.sql_files:
            file = '%s/%s.sql' % (self.sql_path, item)

            print('执行SQL文件 [%s]...' % file)
            with open(file, mode='r', encoding='utf-8') as sql:
                database.comb.execute(sql.read())

    def update(self, refresh=True, cache=False):
        print('准备开始全量更新...')
        time_rec = TimeRecord()

        if self.network is False:
            cache = True
            print('网络配置关闭...')

        self.download_resource(cache)
        # self.download_sql_file(cache)
        # self.exec_sql_file()

        if refresh:
            print('删除历史数据...')
            database.operator.delete_all_data()
            database.material.delete_all_data()

        print('开始更新干员数据...')
        operators = self.init_operators()
        for index, item in enumerate(operators):
            print('保存干员 [%d/%d][%s]...' % (index + 1, len(operators), item.name), end='')
            self.save_operator_data(item)
        avatars, photo, skills, skins = self.save_operator_photo(operators)

        print('开始更新敌人数据...')
        enemies = self.save_enemies_photo()

        print('开始更新材料数据...')
        materials = self.save_materials_data()

        print('开始更新关卡数据...')
        stages = self.save_stages_data()

        totals = (time_rec.total(),
                  len(operators),
                  avatars,
                  photo,
                  skills,
                  skins,
                  enemies,
                  materials,
                  stages)
        message = '数据更新完毕，总耗时%s' \
                  '\n -- %s 位干员' \
                  '\n -- %s 个干员头像' \
                  '\n -- %s 张干员半身照' \
                  '\n -- %s 个技能图标' \
                  '\n -- %s 张干员皮肤' \
                  '\n -- %s 张敌人图片' \
                  '\n -- %s 个材料' \
                  '\n -- %s 个关卡' % totals

        print('\n' + message)
        return message
