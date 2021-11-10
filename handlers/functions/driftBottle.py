import time
import json

from core import Message, Chain
from core.database.models import DriftBottle as DriftBottleBase
from handlers.constraint import FuncInterface
from peewee import fn

bottle_keywords = ['瓶子', '漂流瓶']
throw_keywords = ['扔', '丢']
get_keywords = ['捞', '捡']


class DriftBottle(FuncInterface):
    def __init__(self):
        super().__init__(function_id='drift')

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
                DriftBottleBase.insert(user_id=data.user_id,
                                       group_id=data.group_id,
                                       msg=json.dumps(data.raw_chain),
                                       msg_time=time.time()).execute()
                return reply.text('阿米娅已经帮博士将漂流瓶寄出啦！期待有缘人能拾到它~')

        for item in get_keywords:
            if item in data.text:
                bottle_list = DriftBottleBase.select().where(
                    DriftBottleBase.is_picked is False,
                    DriftBottleBase.is_banned is False).order_by(fn.Random()).limit(1)
                if not bottle_list:
                    return reply.text('阿米娅搜寻了半天，也没有找到更多的漂流瓶……')

                bottle = bottle_list[0]
                # msg是完整的消息原文，raw_chain
                chain = json.loads(bottle.msg)
                # 删掉'兔兔扔瓶子'的内容
                start_index = 0
                for chain_item in chain:
                    if chain_item['type'] == 'Plain':
                        content = chain_item['text']

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

                        chain_item['text'] = content
                        break
                    start_index += 1
                chain = chain[start_index:]

                DriftBottleBase.update(
                    get_user_id=data.user_id,
                    get_group_id=data.group_id,
                    get_time=time.time(),
                    is_picked=True).where(DriftBottleBase.drift_id == bottle.drift_id).execute()

                reply.text('阿米娅拾到了一只漂流瓶，里面写着：')
                reply.chain += chain
                return reply
