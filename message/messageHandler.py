import json
import time
import copy
import random

from functions.functionsIndex import FunctionsIndex
from database.baseController import BaseController
from message.noticeHandler import NoticeHandler
from message.replies import Replies
from library.baiduCloud import NaturalLanguage
from library.numberTranslate import chinese_to_digits
from modules.network.httpRequests import HttpRequests
from modules.commonMethods import Reply

with open('config.json') as config:
    config = json.load(config)

with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)

NLP = NaturalLanguage(config['baidu_cloud'])
database = BaseController()
function = FunctionsIndex()
notice = NoticeHandler()


class MessageHandler(HttpRequests, Replies):
    def __init__(self):
        super().__init__()
        Replies.__init__(self)

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
            notice.on_notice(message)
            return False

        # 重组消息对象，为了更易用
        data = self.rebuild_message(message)

        # 过滤消息
        if self.message_filter(data) is False:
            return False

        on_call = self.on_call(data['text'], data['is_at'])

        # 输出记录
        if on_call:
            self.print_log(data)

        # 处理函数列表（有先后顺序）
        reply_func = [
            {
                # 打招呼
                'func': self.greeting,
                'need_call': False
            },
            {
                # 等待事件
                'func': self.waiting,
                'need_call': False
            },
            {
                # 管理员指令
                'func': self.admin,
                'need_call': True
            },
            {
                # 表情包
                'func': self.faceImage,
                'need_call': True
            },
            {
                # 信赖事件
                'func': self.emotion,
                'need_call': True
            },
            {
                # 使用功能
                'func': function.action,
                'need_call': True,
                'without_call': True
            },
            {
                # 自然语言处理
                'func': self.natural_language_processing,
                'need_call': True
            }
        ]

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
        message = ''
        message_chain = None

        if isinstance(content, str):
            message = content
        elif isinstance(content, list):
            message_chain = content

        database.user.update_user(data['user_id'], res.feeling,
                                  sign=res.sign,
                                  coupon=res.coupon,
                                  message_num=1)

        if message or message_chain:
            self.send_message(data, message, message_chain=message_chain, at=res.at)

    def message_filter(self, data):
        if data is False:
            return False

        limit = config['message']['limit']
        close_beta = config['close_beta']

        if close_beta['enable']:
            if str(data['group_id']) != str(close_beta['group_id']):
                return False

        for item in ['Q群管家', '小冰']:
            if item in data['text']:
                return False

        message_speed = database.message.check_message_speed_by_user(data['user_id'], limit['seconds'])
        if message_speed and message_speed >= limit['max_count']:
            self.send_reply(data, Reply('博士说话太快了，请再慢一些吧～', at=False))
            return False

        return True

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
            'user_id': message['sender']['id'],
            'is_at': False
        }

        if message['type'] == 'FriendMessage':
            # todo 不接受私聊消息
            return False
        elif message['type'] == 'GroupMessage':
            data['type'] = 'group'
            data['nickname'] = message['sender']['memberName']
            data['group_id'] = message['sender']['group']['id']
        else:
            return False

        for chain in message['messageChain']:
            if chain['type'] == 'At' and chain['target'] == config['self_id']:
                data['is_at'] = True
            if chain['type'] == 'Plain':
                text = chain['text'].strip()
                data['text'] = text
                data['text_digits'] = chinese_to_digits(text)
            if chain['type'] == 'Image':
                data['image'] = chain['url'].strip()

        return data

    @staticmethod
    def natural_language_processing(message):
        result = None
        try:
            result = NLP.emotion(message)
        except Exception as e:
            print('NLP', e)

        if result:
            item = result['items'][0]
            text = ''

            if 'replies' in item and item['replies']:
                text = random.choice(item['replies'])

            label = item['label']
            if label == 'neutral':
                pass
            elif label == 'optimistic':
                text = '虽然听不懂博士在说什么，但阿米娅能感受到博士现在高兴的心情，欸嘿嘿……'
            elif label == 'pessimistic':
                text = '博士心情不好吗？阿米娅不懂怎么安慰博士，但阿米娅会默默陪在博士身边的'

            return Reply(text)
