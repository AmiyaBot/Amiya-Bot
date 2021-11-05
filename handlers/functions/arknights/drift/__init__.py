import time

from core import Message, Chain
from core.util.common import word_in_sentence
from dataSource import DataSource
from handlers.constraint import FuncInterface
from core.database.models import DriftBottle
from peewee import fn

bottle_keywords = ['瓶子', '漂流瓶']
throw_keywords = ['扔', '丢']
get_keywords = ['捞', '捡']


class Drift(FuncInterface):
    def __init__(self, data_source: DataSource):
        super().__init__(function_id='drift')
        self.data = data_source

    @FuncInterface.is_disable
    def verify(self, data: Message):
        for item in bottle_keywords:
            if item in data.text:
                return 10

    @FuncInterface.is_used
    def action(self, data: Message):
        reply = Chain(data)

        for item in throw_keywords:
            if item in data.text:
                DriftBottle.insert(user_id=data.user_id,
                                   group_id=data.group_id,
                                   msg=data.text_origin,
                                   msg_time=time.time()).execute()
                return reply.text('阿米娅已经帮博士将漂流瓶寄出啦！期待有缘人能拾到它~')

        for item in get_keywords:
            if item in data.text:
                bottle_list = DriftBottle.select().where(
                    DriftBottle.is_picked == False,
                    DriftBottle.is_banned == False).order_by(fn.Random()).limit(1)
                if not bottle_list:
                    return reply.text('阿米娅搜寻了半天，也没有找到更多的漂流瓶……')

                bottle = bottle_list[0]
                # msg是完整的消息原文，例如'阿米娅扔瓶子 陌生人你好'。输出的时候再处理下把内容头去掉
                content = bottle.msg
                for bottle_key in bottle_keywords:
                    bottle_pos = content.find(bottle_key)
                    if bottle_pos != -1:
                        bottle_pos += len(bottle_key)
                        break
                for throw_key in throw_keywords:
                    throw_pos = content.find(throw_key)
                    if throw_pos != -1:
                        throw_pos += len(throw_key)
                        break
                content = content[max(bottle_pos, throw_pos):]
                if content and content[0] in [':', '：', ' ', ',', '，', '、', '.', '。']:
                    content = content[1:]

                DriftBottle.update(
                    get_user_id=data.user_id,
                    get_group_id=data.group_id,
                    get_time=time.time(),
                    is_picked=True).where(
                        DriftBottle.drift_id == bottle.drift_id).execute()
                return reply.text('阿米娅拾到了一只漂流瓶，里面写着：').text(content)
