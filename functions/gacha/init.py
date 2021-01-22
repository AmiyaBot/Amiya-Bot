import re

from database.baseController import BaseController
from modules.commonMethods import Reply, word_in_sentence

from .gacha import GaCha

database = BaseController()

re_list = [
    "抽卡\\d+次",
    "寻访\\d+次",
    "抽\\d+次",
    "\\d+次寻访",
    "\\d+连寻访",
    "\\d+连抽",
    "\\d+连",
    "\\d+抽"
]


class Init:
    def __init__(self):
        self.function_id = 'gacha'
        self.keyword = ['抽', '连', '寻访', '保底', '卡池']

        self.all_pools = database.user.get_gacha_pool()

    def action(self, data):

        user_id = data['user_id']
        message = data['text_digits']
        message_ori = data['text']

        gacha = GaCha(user_id)

        for item in re_list:
            r = re.search(re.compile(item), message)
            if r:
                times = int(find_once(r'\d+', find_once(item, message)))

                if times <= 0:
                    return Reply('博士在捉弄阿米娅吗 >.<')
                if times > 300:
                    return Reply('博士不要着急，罗德岛的资源要好好规划使用哦，先试试 300 次以内的寻访吧 (#^.^#)')

                user = database.user.get_user(user_id)
                coupon = user[3] if user else 0
                if times > coupon:
                    return Reply('博士，您的寻访凭证（%d张）不够哦~' % coupon)

                if times <= 10:
                    res = gacha.detailed_mode(times)
                else:
                    res = gacha.continuous_mode(times)

                return Reply(res)

        if '保底' in message:
            return Reply(gacha.check_break_even())

        if word_in_sentence(message, ['多少', '几']):
            user = database.user.get_user(user_id)
            coupon = user[3] if user else 0
            text = '博士的寻访凭证还剩余 %d 张~' % coupon
            if coupon:
                text += '\n博士，快去获得您想要的干员吧 ☆_☆'
            return Reply(text)

        if word_in_sentence(message_ori, ['切换', '更换']):
            r = re.search(r'(\d+)', message_ori)
            if r:
                idx = int(r.group(1)) - 1
                if 0 <= idx < len(self.all_pools):
                    message_ori = self.all_pools[idx][1]
            return self.change_pool(user_id, message_ori)

        if word_in_sentence(message, ['查看', '列表']):
            return self.pool_list()

        if word_in_sentence(message, ['抽', '寻访']):
            return Reply('博士是想抽卡吗？和阿米娅说「阿米娅抽卡 N 次」或「阿米娅 N 连抽」就可以了')

    def pool_list(self):
        text = '博士，这是可更换的卡池列表：\n\n'
        pools = []
        max_len = 0
        for index, item in enumerate(self.all_pools):
            pool = '%s [ %s ]' % (('' if index + 1 >= 10 else '0') + str(index + 1), item[1])
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
        return Reply(text)

    def change_pool(self, user_id, message):
        for item in self.all_pools:
            if item[1] in message:
                database.user.set_gacha_pool(user_id, item[0])
                text = ['博士的卡池已切换为【%s】\n' % item[1]]
                if item[2]:
                    text.append('[★★★★★★] %s' % item[2].replace(',', '、'))
                if item[3]:
                    text.append('[★★★★★　] %s' % item[3].replace(',', '、'))
                if item[4]:
                    text.append('[☆☆☆☆　　] %s' % item[4].replace(',', '、'))
                text = '\n'.join(text)
                return Reply(text)
        return Reply('博士，没有找到这个卡池哦')


def find_once(reg, text):
    r = re.compile(reg)
    f = r.findall(text)
    if len(f):
        return f[0]
    return ''
