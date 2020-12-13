import json
import random

from database.baseController import BaseController
from modules.commonMethods import insert_empty

database = BaseController()


class GaCha:
    def __init__(self, user_id):

        pool_list = database.user.get_gacha_pool(user_id=user_id)
        if bool(pool_list) is False:
            pool_list = database.user.get_gacha_pool()
        pool = pool_list[0]
        operators = database.operator.get_gacha_operator(pool[2].split(',') if pool[5] == 1 else None)

        class_group = {}
        for item in operators:
            if item[2] not in class_group:
                class_group[item[2]] = {}
            class_group[item[2]][item[1]] = {
                'name': item[1],
                'rarity': item[2]
            }

        self.user_id = user_id
        self.operator = class_group
        self.pick_up_name = pool[1]
        self.pick_up = {
            6: [i for i in pool[2].split(',') if i != ''],
            5: [i for i in pool[3].split(',') if i != ''],
            4: [i for i in pool[4].split(',') if i != '']
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
        pickup_hit = {
            5: 0,
            6: 0
        }
        high_star = {
            5: {},
            6: {}
        }

        ten_gacha = []
        purple_pack = 0
        multiple_rainbow = {}

        result = '阿米娅给博士扔来了%d张【%s】简历，博士细细地检阅着...\n' % (times, self.pick_up_name)

        for item in operators:
            rarity = item['rarity']
            name = item['name']

            # 记录抽到的各星级干员的数量
            rarity_sum[rarity - 3] += 1

            # 记录抽中的 pickup 干员数量
            if (rarity in self.pick_up) and (rarity in pickup_hit):
                if name in self.pick_up[rarity]:
                    pickup_hit[rarity] += 1

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

        if pickup_hit[6] > 0:
            result += '\n抽到UP的六星干员了，今天也是欧气满满的呀！'
        else:
            if rarity_sum[3] > 0:
                result += '\n没有抽到UP的六星干员吗？不知道其他六星是不是博士想要的呢'
            else:
                result += '\n没有抽到六星干员吗？博士不要气馁，我们要一起氪服困难！'

        result += '\n%s' % self.check_break_even()

        return result

    def detailed_mode(self, times):
        operators = self.start_gacha(times)

        result = '阿米娅给博士扔来了%d张【%s】简历，博士细细地检阅着...\n\n' % (times, self.pick_up_name)

        no_high_rarity = True
        six_rarity = 0

        text = ''
        hit = False

        for item in operators:
            star = '☆' if item['rarity'] < 5 else '★'
            result += '%s%s\n' % (insert_empty(item['name'], 5, True), star * item['rarity'])

            if item['rarity'] >= 5:
                no_high_rarity = False

            if item['rarity'] == 6:
                six_rarity += 1
                if 6 in self.pick_up:
                    if item['name'] in self.pick_up[6]:
                        text = '\n抽到UP的六星干员了，今天也是欧气满满的呀！'
                        hit = True
                    else:
                        if hit is False:
                            text = '\n抽到六星干员了，是不是博士想要的呢？'

        result += text

        if six_rarity:
            if six_rarity > 1:
                result += '\n博士，竟然有 %d 个六星干员！简直是太棒了！' % six_rarity
        else:
            if no_high_rarity:
                result += '\n啊这……博士，不管抽到什么干员，相信他们总有发光发热的一天的'
            else:
                result += '\n博士，资深干员们都有各自出色的地方，要善用他们哦'

        result += '\n%s' % self.check_break_even()

        return result

    def check_break_even(self):
        user = database.user.get_user(self.user_id)
        break_even = user[4]
        break_even_rate = 98
        if break_even > 50:
            break_even_rate -= (break_even - 50) * 2

        return '距离上一次抽出六星已经进行了 %d 抽，当前抽出六星的概率为 %d' % (break_even, 100 - break_even_rate) + '%'

    def start_gacha(self, times):
        operators = []

        user = database.user.get_user(self.user_id)
        break_even = user[4]

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
        operator_list = list(self.operator[rarity].keys())

        if rarity in self.pick_up and self.pick_up[rarity]:
            for name in self.pick_up[rarity]:
                if name in operator_list:
                    operator_list.remove(name)

            group = [self.pick_up[rarity]]
            group += [operator_list] * (4 if rarity == 4 else 1)

            return random.choice(random.choice(group))

        return random.choice(operator_list)
