import os
import random

from library.imageCreator import create_gacha_result
from database.baseController import BaseController
from modules.commonMethods import insert_empty
from message.messageType import TextImage, Image

database = BaseController()
avatar_resource = 'resource/images/avatars'
gacha_result = 'resource/message/Gacha'

class_index = {
    1: 'PIONEER',
    2: 'WARRIOR',
    3: 'TANK',
    4: 'SNIPER',
    5: 'CASTER',
    6: 'SUPPORT',
    7: 'MEDIC',
    8: 'SPECIAL'
}


def get_temp_operator():
    operators = {}
    temp_path = 'resource/tempOperator.txt'
    if os.path.exists(temp_path):
        with open(temp_path, mode='r', encoding='utf-8') as tp:
            ct = [item.split(',') for item in tp.read().strip('\n').split('\n')]
            for item in ct:
                operators[item[0]] = {
                    'photo': 'None',
                    'rarity': item[1],
                    'class': class_index[int(item[2])].lower()
                }
    return operators


class GaCha:
    def __init__(self, user_id):

        pool = database.user.get_gacha_pool(user_id=user_id)
        if bool(pool) is False:
            pool_list = database.user.get_gacha_pool()
            pool = pool_list[0]

        special = pool['pickup_s'].split(',') if pool['pickup_s'] else []
        weight = {}
        for item in special:
            item = item.split('|')
            weight[item[0]] = int(item[1])

        operators = database.operator.get_gacha_operator(extra=weight.keys())

        class_group = {}
        for item in operators:
            rarity = item['operator_rarity']
            name = item['operator_name']
            if rarity not in class_group:
                class_group[rarity] = {}
            class_group[rarity][name] = {
                'name': name,
                'rarity': rarity,
                'weight': weight[name] if name in weight else 1
            }

        self.user_id = user_id
        self.operator = class_group
        self.temp_operator = get_temp_operator()
        self.limit_pool = pool['limit_pool']
        self.pick_up_name = pool['pool_name']
        self.pick_up = {
            6: [i for i in pool['pickup_6'].split(',') if i != ''],
            5: [i for i in pool['pickup_5'].split(',') if i != ''],
            4: [i for i in pool['pickup_4'].split(',') if i != '']
        }
        self.rarity_range = {
            1: 3,
            41: 4,
            91: 5,
            99: 6
        }
        '''
        概率：
        3 星 40% 区间为 1 ~ 40
        4 星 50% 区间为 41 ~ 90
        5 星 8% 区间为 91 ~ 98
        6 星 2% 区间为 99 ~ 100
        '''

    def continuous_mode(self, times):
        operators = self.start_gacha(times)

        rarity_sum = [0, 0, 0, 0]
        high_star = {
            5: {},
            6: {}
        }

        ten_gacha = []
        purple_pack = 0
        multiple_rainbow = {}

        result = '阿米娅给博士扔来了%d张简历，博士细细地检阅着...\n\n【%s】\n' % (times, self.pick_up_name)

        for item in operators:
            rarity = item['rarity']
            name = item['name']

            # 记录抽到的各星级干员的数量
            rarity_sum[rarity - 3] += 1

            # 记录抽中的高星干员
            if rarity >= 5:
                if name not in high_star[rarity]:
                    high_star[rarity][name] = 0
                high_star[rarity][name] += 1

            # 记录每十连的情况
            ten_gacha.append(rarity)
            if len(ten_gacha) >= 10:

                five = ten_gacha.count(5)
                six = ten_gacha.count(6)

                if five == 0 and six == 0:
                    purple_pack += 1

                if six > 1:
                    if six not in multiple_rainbow:
                        multiple_rainbow[six] = 0
                    multiple_rainbow[six] += 1
                ten_gacha = []

        for r in high_star:
            sd = high_star[r]
            if sd:
                result += '\n%s\n' % ('★' * r)
                operator_num = {}
                for i in sorted(sd, key=sd.__getitem__, reverse=True):
                    num = high_star[r][i]
                    if num not in operator_num:
                        operator_num[num] = []
                    operator_num[num].append(i)
                for num in operator_num:
                    result += '%s X %d\n' % ('、'.join(operator_num[num]), num)

        if rarity_sum[2] == 0 and rarity_sum[3] == 0:
            result += '\n然而并没有高星干员...'

        result += '\n三星：%s四星：%d\n五星：%s六星：%d\n' % (
            insert_empty(rarity_sum[0], 4),
            rarity_sum[1],
            insert_empty(rarity_sum[2], 4),
            rarity_sum[3])

        enter = True
        if purple_pack > 0:
            result += '\n'
            enter = False
            result += '出现了 %d 次十连紫气东来\n' % purple_pack
        for num in multiple_rainbow:
            if enter:
                result += '\n'
                enter = False
            result += '出现了 %d 次十连内 %d 个六星\n' % (multiple_rainbow[num], num)

        result += '\n%s' % self.check_break_even()

        return TextImage(result)

    def detailed_mode(self, times, ten_times=False):
        operators = self.start_gacha(times)

        result = '阿米娅给博士扔来了%d张简历，博士细细地检阅着...\n\n【%s】\n\n' % (times, self.pick_up_name)

        operators_data = database.operator.get_all_operator([item['name'] for item in operators])
        operator_avatars = {item['operator_name']: item['operator_avatar'] for item in operators_data}

        icons = []
        for index, item in enumerate(operators):
            star = '☆' if item['rarity'] < 5 else '★'
            result += '%s%s%s\n\n' % (' ' * 15, insert_empty(item['name'], 6, True), star * item['rarity'])

            if item['name'] in operator_avatars:
                avatar_path = '%s/%s.png' % (avatar_resource, operator_avatars[item['name']])
                if os.path.exists(avatar_path):
                    icons.append({
                        'path': avatar_path,
                        'size': (34, 34),
                        'pos': (10, 60 + 34 * index)
                    })

        result += '\n%s' % self.check_break_even()

        reply = [TextImage(result, icons)]
        if ten_times:
            operators_info = {
                item['operator_name']: {
                    'photo': item['operator_avatar'],
                    'rarity': item['operator_rarity'],
                    'class': class_index[item['operator_class']].lower()
                } for item in operators_data
            }
            result_list = []

            for item in operators:
                name = item['name']
                op_dt = None

                if name in operators_info:
                    op_dt = operators_info[name]
                elif name in self.temp_operator:
                    op_dt = self.temp_operator[name]

                result_list.append(op_dt)

            res_img = '%s/%s' % (gacha_result, create_gacha_result(result_list))
            reply.insert(0, Image(res_img))

        return reply

    def check_break_even(self):
        user = database.user.get_user(self.user_id)
        break_even = user['gacha_break_even']
        break_even_rate = 98
        if break_even > 50:
            break_even_rate -= (break_even - 50) * 2

        return '已经抽取了 %d 次而未获得六星干员\n当前抽出六星干员的概率为 %d' % (break_even, 100 - break_even_rate) + '%'

    def start_gacha(self, times):
        operators = []

        user = database.user.get_user(self.user_id)
        break_even = user['gacha_break_even']

        for i in range(0, times):

            random_num = random.randint(1, 100)
            rarity = 0
            break_even_rate = 98

            for less in self.rarity_range:
                if random_num >= less:
                    rarity = self.rarity_range[less]

            break_even += 1

            if break_even > 50:
                break_even_rate -= (break_even - 50) * 2

            if random_num >= break_even_rate:
                rarity = 6

            if rarity == 6:
                break_even = 0

            operator = self.get_operator(rarity)

            operators.append({
                'rarity': rarity,
                'name': operator
            })

        database.user.set_break_even(self.user_id, break_even, times)
        return operators

    def get_operator(self, rarity):
        operator_list = []
        for name, item in self.operator[rarity].items():
            for w in range(item['weight']):
                operator_list.append(name)

        if rarity in self.pick_up and self.pick_up[rarity]:
            for name in self.pick_up[rarity]:
                if name in operator_list:
                    operator_list.remove(name)

            group = [self.pick_up[rarity]]
            group += [operator_list] * (4 if rarity == 4 else 1)

            special = {
                6: {
                    1: lambda g: g[int((random.randint(1, 100) + 1) / 70)],
                    2: lambda g: g[0]
                },
                5: {
                    2: lambda g: g[0]
                }
            }

            if rarity in special and self.limit_pool in special[rarity]:
                choice = special[rarity][self.limit_pool](group)
            else:
                choice = random.choice(group)

            return random.choice(choice)

        return random.choice(operator_list)
