import sys
import json
import time
import copy
import threading

from message.replies import reply_func_list
from message.eventsHandler import EventsHandler
from database.baseController import BaseController
from library.numberTranslate import chinese_to_digits
from modules.network.httpRequests import HttpRequests
from modules.commonMethods import Reply, text_to_pinyin
from modules.config import get_config

config = get_config()
database = BaseController()
events = EventsHandler()
amiya_name = database.config.get_amiya_name()


class MessageHandler(HttpRequests):
    def __init__(self):
        super().__init__()

        self.message_stack = []

        threading.Thread(target=self.save_message).start()

    def on_message(self, message):

        # 过滤未知的消息
        if 'type' not in message:
            try:
                date = time.strftime('%Y%m%d%H%M%S', time.localtime())
                with open('remind/unknown_%s.txt' % date, mode='w+') as unknown:
                    unknown.write(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print('Remind', e)
            return False

        # 过滤非聊天的消息
        if message['type'] not in ['GroupMessage', 'FriendMessage']:
            events.on_events(message)
            return False

        # 重组消息对象
        data = self.rebuild_message(message)

        # 过滤消息
        if self.message_filter(data) is False:
            return False

        on_call = self.on_call(data['text'], data['is_at'])

        # 输出记录
        if on_call:
            self.print_log(data)
            database.message.add_message(
                msg_type='call',
                user_id=data['user_id'],
                group_id=data['group_id']
            )

        # 处理函数列表
        reply_func = reply_func_list(data)

        # 遍历处理函数直至获得回复为止
        for action in reply_func:
            if action['need_call'] and on_call is False:
                continue

            self_data = copy.deepcopy(data)

            if 'without_call' in action and action['without_call']:
                # 去掉称呼
                for name in amiya_name[0]:
                    if self_data['text'].find(name) == 0:
                        self_data['text'] = self_data['text'].replace(name, '', 1)
                        self_data['text_digits'] = self_data['text_digits'].replace(name, '', 1)
                        break

            result = action['func'](self_data)
            if result:
                if isinstance(result, list):
                    for item in result:
                        self.send_reply(self_data, item)
                else:
                    self.send_reply(self_data, result)
                break

    def send_reply(self, data, res):
        if isinstance(res, Reply) is False:
            return False

        content = res.content
        database.user.update_user(data['user_id'], res.feeling,
                                  sign=res.sign,
                                  coupon=res.coupon,
                                  message_num=1)

        if len(sys.argv) > 1 and sys.argv[1] == 'Test':
            print(content)
            return False

        self.send_message(data, message_chain=content, at=res.at)

    def message_filter(self, data):
        if data is False:
            return False

        limit = config['message']['limit']
        close_beta = config['close_beta']

        # 封闭测试
        if 'group_id' in data and close_beta['enable']:
            if str(data['group_id']) != str(close_beta['group_id']):
                return False

        # 屏蔽官方机器人
        for item in ['Q群管家', '小冰']:
            if item in data['text']:
                return False

        # 屏蔽黑名单用户
        is_black = database.user.get_black_user(data['user_id'])
        if is_black:
            return False

        if data['type'] == 'group':
            self.message_stack.append({
                'msg_type': 'talk',
                'group_id': data['group_id'],
                'user_id': data['user_id'],
                'reply_user': 0,
                'msg_time': int(time.time())
            })

        # 消息速度限制
        message_speed = database.message.check_message_speed_by_user(data['user_id'], limit['seconds'])
        if message_speed and message_speed >= limit['max_count']:
            self.send_reply(data, Reply('博士说话太快了，请再慢一些吧～', at=False))
            return False

        return True

    def save_message(self):
        while True:
            if self.message_stack:
                database.message.batch_add_message(self.message_stack)
                self.message_stack = []
            time.sleep(60)

    @staticmethod
    def on_call(text, at):
        for name in amiya_name[0]:
            if text.find(name) == 0:
                return True
        return at

    @staticmethod
    def print_log(data):
        print('[%s][%s]%s[UID %s][%s] %s' % (
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            data['type'],
            ('[GID %s]' % data['group_id']) if 'group_id' in data else '',
            data['user_id'],
            data['nickname'],
            data['text']
        ))

    @staticmethod
    def rebuild_message(message):
        data = {
            'text': '',
            'text_digits': '',
            'text_pinyin': '',
            'user_id': message['sender']['id'],
            'is_at': False
        }

        if message['type'] == 'FriendMessage':
            # todo 仅限管理员使用私聊
            if data['user_id'] != config['admin_id']:
                return False
            data['type'] = 'friend'
            data['nickname'] = message['sender']['nickname']
        elif message['type'] == 'GroupMessage':
            data['type'] = 'group'
            data['nickname'] = message['sender']['memberName']
            data['group_id'] = message['sender']['group']['id']
            data['permission'] = message['sender']['permission']
        else:
            return False

        for chain in message['messageChain']:
            if chain['type'] == 'At' and chain['target'] == config['self_id']:
                data['is_at'] = True
            if chain['type'] == 'Plain':
                text = chain['text'].strip()
                data['text'] = text
                data['text_digits'] = chinese_to_digits(text)
                data['text_pinyin'] = text_to_pinyin(text)
            if chain['type'] == 'Image':
                data['image'] = chain['url'].strip()

        return data
