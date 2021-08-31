import re

from core import Message, Chain
from core.util.common import word_in_sentence
from dataSource import DataSource
from handlers.funcInterface import FuncInterface

from .gacha import GachaForUser, GachaPool

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


class Gacha(FuncInterface):
    def __init__(self, data_source: DataSource):
        super().__init__(function_id='gacha')

        self.data = data_source
        self.pool = GachaPool()

    @FuncInterface.is_disable
    def check(self, data: Message):
        for item in ['抽', '连', '寻访', '保底', '卡池']:
            if item in data.text:
                return True
        return False

    @FuncInterface.is_used
    def action(self, data: Message):

        GC = GachaForUser(data, self.data)

        coupon = data.user_info.coupon
        message = data.text_digits
        message_ori = data.text

        reply = Chain(data)

        for item in re_list:
            r = re.search(re.compile(item), message)
            if r:
                times = int(find_once(r'\d+', find_once(item, message)))

                if times <= 0:
                    return reply.text('博士在捉弄阿米娅吗 >.<')
                if times > 300:
                    return reply.text('博士不要着急，罗德岛的资源要好好规划使用哦，先试试 300 次以内的寻访吧 (#^.^#)')
                if times > coupon:
                    return reply.text('博士，您的寻访凭证（%d张）不够哦~' % coupon)

                if times <= 10:
                    return GC.detailed_mode(times, ten_times=times == 10)
                else:
                    return GC.continuous_mode(times)

        if '保底' in message:
            return reply.text(GC.check_break_even())

        if word_in_sentence(message, ['多少', '几']):
            text = '博士的寻访凭证还剩余 %d 张~' % coupon
            if coupon:
                text += '\n博士，快去获得您想要的干员吧 ☆_☆'
            return reply.text(text)

        if word_in_sentence(message_ori, ['切换', '更换']):
            r = re.search(r'(\d+)', message_ori)
            if r:
                idx = int(r.group(1)) - 1
                if 0 <= idx < len(self.pool.all_pools):
                    message_ori = self.pool.all_pools[idx].pool_name

            return reply.text(
                self.pool.change_pool(
                    user_id=None if data.is_admin and '所有人' in message else data.user_id,
                    message=message_ori
                ),
                trans_image=False
            )

        if word_in_sentence(message, ['查看', '卡池', '列表']):
            return reply.text_image(self.pool.pool_list())

        if word_in_sentence(message, ['抽', '寻访']):
            return reply.text('博士是想抽卡吗？试试和阿米娅说「阿米娅抽卡 N 次」或「阿米娅 N 连抽」吧')


def find_once(reg, text):
    r = re.compile(reg)
    f = r.findall(text)
    if len(f):
        return f[0]
    return ''
