import os
import random

from core import Message, Chain
from core.database.models import User, Pool
from core.util.common import insert_empty
from core.util.imageCreator import create_gacha_result
from dataSource import GameData, Operator

avatar_resource = 'resource/images/avatars'
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


class GachaForUser:
    def __init__(self, data: Message, game_data: GameData):
        self.data = data
        self.game_data = game_data

        pool = Pool.get_by_id(data.user_info.gacha_pool)

        special = pool.pickup_s.split(',') if pool.pickup_s else []
        weight = {}
        for item in special:
            item = item.split('|')
            weight[item[0]] = int(item[1])

        operators = self.__get_gacha_operator(
            extra=list(weight.keys())
        )
        class_group = {}

        for item in operators:
            rarity = item.rarity
            name = item.name
            if rarity not in class_group:
                class_group[rarity] = {}
            class_group[rarity][name] = {
                'name': name,
                'rarity': rarity,
                'weight': weight[name] if name in weight else 1
            }

        self.operator = class_group
        self.temp_operator = self.__get_temp_operator()
        self.break_even = self.data.user_info.gacha_break_even
        self.limit_pool = pool.limit_pool
        self.pick_up_name = pool.pool_name
        self.pick_up = {
            6: [i for i in pool.pickup_6.split(',') if i != ''],
            5: [i for i in pool.pickup_5.split(',') if i != ''],
            4: [i for i in pool.pickup_4.split(',') if i != '']
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

    def __get_gacha_operator(self, extra):
        opts = []
        for name, item in self.game_data.operators.items():
            if name in extra or (item.rarity >= 3 and not item.limit and not item.unavailable):
                opts.append(item)
        return opts

    @staticmethod
    def __get_temp_operator():
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

        return Chain(self.data).text_image(result)

    def detailed_mode(self, times, ten_times=False):
        operators = self.start_gacha(times)
        operators_info = {}

        reply = Chain(self.data)

        result = f'阿米娅给博士扔来了{times}张简历，博士细细地检阅着...\n\n【{self.pick_up_name}】\n\n'
        icons = []

        for index, item in enumerate(operators):
            name = item['name']
            rarity = item['rarity']
            star = '☆' if rarity < 5 else '★'
            result += '%s%s%s\n\n' % (' ' * 15, insert_empty(name, 6, True), star * rarity)

            if name in self.game_data.operators:
                opt: Operator = self.game_data.operators[name]
                avatar_path = '%s/%s.png' % (avatar_resource, opt.id)

                if os.path.exists(avatar_path):
                    icons.append({
                        'path': avatar_path,
                        'size': (34, 34),
                        'pos': (10, 60 + 34 * index)
                    })

                operators_info[name] = {
                    'photo': opt.id,
                    'rarity': opt.rarity,
                    'class': class_index[opt.classes_code].lower()
                }

        result += '\n%s' % self.check_break_even()

        if ten_times:
            result_list = []

            for item in operators:
                name = item['name']
                op_dt = None

                if name in operators_info:
                    op_dt = operators_info[name]
                elif name in self.temp_operator:
                    op_dt = self.temp_operator[name]

                result_list.append(op_dt)

            reply.image(create_gacha_result(result_list))

        return reply.text_image(result, icons)

    def check_break_even(self):
        break_even_rate = 98
        if self.break_even > 50:
            break_even_rate -= (self.break_even - 50) * 2

        return f'当前已经抽取了 {self.break_even} 次而未获得六星干员\n下次抽出六星干员的概率为 {100 - break_even_rate}%'

    def start_gacha(self, times):
        operators = []

        for i in range(0, times):

            random_num = random.randint(1, 100)
            rarity = 0
            break_even_rate = 98

            for less in self.rarity_range:
                if random_num >= less:
                    rarity = self.rarity_range[less]

            self.break_even += 1

            if self.break_even > 50:
                break_even_rate -= (self.break_even - 50) * 2

            if random_num >= break_even_rate:
                rarity = 6

            if rarity == 6:
                self.break_even = 0

            operator = self.get_operator(rarity)

            operators.append({
                'rarity': rarity,
                'name': operator
            })

        User.update(gacha_break_even=self.break_even, coupon=User.coupon - times) \
            .where(User.user_id == self.data.user_info.user_id) \
            .execute()

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


class GachaPool:
    def __init__(self):
        self.all_pools = Pool.select()

    def pool_list(self):
        text = '博士，这是可更换的卡池列表：\n\n'
        pools = []
        max_len = 0
        for index, item in enumerate(self.all_pools):
            pool = '%s [ %s ]' % (('' if index + 1 >= 10 else '0') + str(index + 1), item.pool_name)
            if index % 2 == 0 and len(pool) > max_len:
                max_len = len(pool)
            pools.append(pool)

        pools_table = ''
        curr_row = 0
        for index, item in enumerate(pools):
            if index % 2 == 0:
                pools_table += item
                curr_row = len(item)
            else:
                spaces = max_len - curr_row + 2
                pools_table += '%s%s\n' % ('　' * spaces, item)
                curr_row = 0

        if curr_row != 0:
            pools_table += '\n'

        text += pools_table
        text += '\n要切换卡池，请和阿米娅说「阿米娅切换卡池 "卡池名称" 」\n或「阿米娅切换第 N 个卡池」'
        return text

    def change_pool(self, user_id, message):
        for item in self.all_pools:
            if item.pool_name in message:

                task = User.update(gacha_pool=item.pool_id).where(
                    (User.user_id == user_id) if user_id else None
                )
                task.execute()

                text = [
                    f'{"所有" if not user_id else ""}博士的卡池已切换为{"【限定】" if item.limit_pool != 0 else ""}【{item.pool_name}】\n'
                ]
                if item.pickup_6:
                    text.append('[★★★★★★] %s' % item.pickup_6.replace(',', '、'))
                if item.pickup_5:
                    text.append('[★★★★★　] %s' % item.pickup_5.replace(',', '、'))
                if item.pickup_4:
                    text.append('[☆☆☆☆　　] %s' % item.pickup_4.replace(',', '、'))

                return '\n'.join(text)

        return '博士，要告诉阿米娅准确的卡池序号或名称哦'
