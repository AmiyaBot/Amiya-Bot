import os
import random

from io import BytesIO
from PIL import Image, ImageDraw
from core import Message, Chain
from core.database.user import OperatorBox, UserGachaInfo, UserInfo
from core.database.bot import *
from core.util import insert_empty, extract_zip_plugin
from core.resource.arknightsGameData import ArknightsGameData

curr_dir = os.path.dirname(__file__)
gacha_plugin = 'resource/plugins/gacha'

if curr_dir.endswith('.zip'):
    extract_zip_plugin(curr_dir, gacha_plugin)
else:
    gacha_plugin = curr_dir

line_height = 16
side_padding = 10
avatar_resource = 'resource/gamedata/avatar'
color = {
    6: 'FF4343',
    5: 'FEA63A',
    4: 'A288B5',
    3: '7F7F7F',
    2: '7F7F7F',
    1: '7F7F7F'
}


class GachaBuilder:
    def __init__(self, data: Message):
        self.data = data
        self.user_gacha: UserGachaInfo = UserGachaInfo.get_or_create(user_id=data.user_id)[0]

        pool: Pool = Pool.get_by_id(self.user_gacha.gacha_pool)

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
        self.temp_operator = self.__get_temp_operator(pool.id)
        self.break_even = self.user_gacha.gacha_break_even
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

    @staticmethod
    def __get_gacha_operator(extra):
        opts = []
        for name, item in ArknightsGameData.operators.items():
            if name in extra or (item.rarity >= 3 and not item.limit and not item.unavailable):
                opts.append(item)
        return opts

    @staticmethod
    def __get_temp_operator(pool_id):
        operators = {}
        sp: List[PoolSpOperator] = PoolSpOperator.select().where(PoolSpOperator.pool_id == pool_id)
        for item in sp:
            operators[item.operator_name] = {
                'portraits': '',
                'temp_portraits': f'{gacha_plugin}/temp/{item.image}' if item.image else None,
                'rarity': item.rarity,
                'class': item.classes
            }
        return operators

    def continuous_mode(self, times, coupon, point):
        operators = self.start_gacha(times, coupon, point)

        rarity_sum = [0, 0, 0, 0]
        high_star = {
            5: {},
            6: {}
        }

        ten_gacha = []
        purple_pack = 0
        multiple_rainbow = {}

        result = f'阿米娅给博士扔来了{times}张简历，博士细细地检阅着...\n\n【{self.pick_up_name}】\n'

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
                result += f'\n[cl %s@#{color[r]} cle]\n' % ('★' * r)
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
            result += f'出现了 {purple_pack} 次十连紫气东来\n'
        for num in multiple_rainbow:
            if enter:
                result += '\n'
                enter = False
            result += f'出现了 {multiple_rainbow[num]} 次十连内 {num} 个六星\n'

        result += '\n%s' % self.check_break_even()

        return Chain(self.data).text_image(result)

    def detailed_mode(self, times, coupon, point, ten_times=False):
        operators = self.start_gacha(times, coupon, point)
        operators_info = {}

        game_data = ArknightsGameData
        reply = Chain(self.data)

        result = f'阿米娅给博士扔来了{times}张简历，博士细细地检阅着...\n\n【{self.pick_up_name}】\n\n'
        icons = []

        icon_size = 32
        offset = int((line_height * 3 - icon_size) / 2)
        top = side_padding + line_height * 2 + offset + 5

        for index, item in enumerate(operators):
            name = item['name']
            rarity = item['rarity']

            star = f'[cl %s@#{color[rarity]} cle]' % ('★' * rarity)

            result += '%s%s%s\n\n' % (' ' * 15, insert_empty(name, 6, True), star)

            if name in game_data.operators:
                opt = game_data.operators[name]
                avatar_path = f'resource/gamedata/avatar/{opt.id}.png'

                if os.path.exists(avatar_path):
                    icons.append({
                        'path': avatar_path,
                        'size': icon_size,
                        'pos': (side_padding, top + offset + icon_size * index)
                    })

                operators_info[name] = {
                    'portraits': opt.id,
                    'temp_portraits': f'{gacha_plugin}/temp/{opt.name}',
                    'rarity': opt.rarity,
                    'class': opt.classes_code.lower()
                }

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

            reply.image(create_gacha_image(result_list))

            return reply.text(f'【{self.pick_up_name}】\n{self.check_break_even()}')
        else:
            return reply.text_image(f'{result}\n{self.check_break_even()}', icons)

    def check_break_even(self):
        break_even_rate = 98
        if self.break_even > 50:
            break_even_rate -= (self.break_even - 50) * 2

        gacha_info: UserGachaInfo = UserGachaInfo.get_or_none(user_id=self.data.user_id)

        return f'当前已经抽取了 {self.break_even} 次而未获得六星干员\n' \
               f'下次抽出六星干员的概率为 {100 - break_even_rate}%\n' \
               f'剩余寻访凭证 {gacha_info.coupon}'

    def start_gacha(self, times, coupon, point):
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

        UserGachaInfo.update(gacha_break_even=self.break_even, coupon=UserGachaInfo.coupon - coupon) \
            .where(UserGachaInfo.user_id == self.data.user_id) \
            .execute()

        UserInfo.update(jade_point=UserInfo.jade_point - point).where(UserInfo.user_id == self.data.user_id).execute()

        self.set_box(operators)

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

            '''
            特殊卡池类型
                1: 限定
                2: 联合寻访
                3: 前路回响
            '''
            special = {
                6: {
                    1: lambda g: g[int((random.randint(1, 100) + 1) / 70)],
                    2: lambda g: g[0],
                    3: lambda g: g[0]
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

    def set_box(self, result):
        user_box: OperatorBox = OperatorBox.get_or_create(user_id=self.data.user_id)[0]
        box_map = {}

        if user_box.operator:
            for n in user_box.operator.split('|'):
                n = n.split(':')
                box_map[n[0]] = [
                    n[0],
                    int(n[1]),
                    int(n[2])
                ]

        for item in result:
            name = item['name']

            if name in box_map:
                box_map[name][2] += 1
            else:
                box_map[name] = [name, item['rarity'], 1]

        box_res = '|'.join([':'.join([str(i) for i in item]) for n, item in box_map.items()])

        OperatorBox.update(operator=box_res).where(OperatorBox.user_id == self.data.user_id).execute()


def create_gacha_image(result: list):
    image = Image.open(f'{gacha_plugin}/gacha/bg.png')
    draw = ImageDraw.ImageDraw(image)

    x = 78
    for item in result:
        if item is None:
            x += 82
            continue

        rarity = f'{gacha_plugin}/gacha/%s.png' % item['rarity']
        if os.path.exists(rarity):
            img = Image.open(rarity).convert('RGBA')
            image.paste(img, box=(x, 0), mask=img)

        portraits = 'resource/gamedata/portrait/%s_1.png' % item['portraits']
        if not os.path.exists(portraits):
            if 'temp_portraits' in item and item['temp_portraits']:
                portraits = item['temp_portraits']

        if os.path.exists(portraits):
            img = Image.open(portraits).convert('RGBA')

            radio = 252 / img.size[1]

            width = int(img.size[0] * radio)
            height = int(img.size[1] * radio)

            step = int((width - 82) / 2)
            crop = (step, 0, width - step, height)

            img = img.resize(size=(width, height))
            img = img.crop(crop)
            image.paste(img, box=(x, 112), mask=img)

        draw.rectangle((x + 10, 321, x + 70, 381), fill='white')
        class_img = f'{gacha_plugin}/classify/%s.png' % item['class']
        if os.path.exists(class_img):
            img = Image.open(class_img).convert('RGBA')
            img = img.resize(size=(59, 59))
            image.paste(img, box=(x + 11, 322), mask=img)

        x += 82

    x, y = image.size
    image = image.resize((int(x * 0.8), int(y * 0.8)), Image.ANTIALIAS)

    container = BytesIO()
    image.save(container, quality=80, format='PNG')

    return container.getvalue()
