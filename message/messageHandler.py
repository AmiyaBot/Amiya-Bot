import re
import os
import json
import time
import random

from functions.functionsIndex import FunctionsIndex
from database.baseController import BaseController
from message.messageType import MessageType
from message.noticeHandler import NoticeHandler
from library.baiduCloud import NaturalLanguage
from library.numberTranslate import chinese_to_digits_in_sentence
from modules.network.httpRequests import HttpRequests
from modules.commonMethods import Reply, word_in_sentence
from modules.resource.imageManager import ImageManager

from .replies import *

with open('config.json') as config:
    config = json.load(config)
with open('resource/words/amiyaName.json', encoding='utf-8') as file:
    amiya_name = json.load(file)

NLP = NaturalLanguage(config['baidu_cloud'])
database = BaseController()
function = FunctionsIndex()
notice = NoticeHandler()
MSG = MessageType()
IM = ImageManager('resource/images/face/')


class MessageHandler(HttpRequests):
    def __init__(self):
        super().__init__()

        self.images = []
        for root, dirs, files in os.walk('resource/images/face'):
            for item in files:
                if item != '.gitkeep':
                    self.images.append(item)

    def on_message(self, message):

        if 'type' not in message:
            try:
                with open('remind/unknown.txt', mode='w+') as unknown:
                    unknown.write(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print('Remind', e)
            return False

        if message['type'] not in ['GroupMessage', 'FriendMessage']:
            notice.on_notice(message)
            return False

        data = rebuild_message(message)

        if message_filter(data) is False:
            return False

        # target_id = data['group_id'] if data['type'] == 'group' else data['user_id']
        # database.message.add_message(target_id, data['type'])

        if data['is_at'] is False and call_me(data['text']) is False:

            reply = greeting(data)
            if reply and type(reply) is Reply:
                return self.do_reply(data, reply)

            reply = waiting(data)
            if reply and type(reply) is Reply:
                return self.do_reply(data, reply)

            return False

        print('[%s][%s]%s[UID %s][%s] %s' % (
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            data['type'],
            ('[GID %s]' % data['group_id']) if 'group_id' in data else '',
            data['user_id'],
            data['nickname'],
            data['text']
        ))

        data['text'] = chinese_to_digits_in_sentence(data['text'])

        if call_me(data['text'], True) or data['text'] == '':
            self.image_face(data)
        else:
            reply = emotion(data)
            if reply and type(reply) is Reply:
                return self.do_reply(data, reply)

            reply = function.action(data)
            if reply:
                if type(reply) is Reply:
                    self.do_reply(data, reply)
                elif type(reply) is list:
                    for item in reply:
                        self.do_reply(data, item)
                return False

            reply = natural_language_processing(data['text'])
            if reply:
                self.do_reply(data, Reply(reply))

        return False

    def do_reply(self, data, reply):
        message = ''
        message_chain = None

        if type(reply.content) is str:
            message = reply.content
        elif type(reply.content) is list:
            message_chain = reply.content

        database.user.add_feeling(data['user_id'], reply.feeling, reply.sign)

        if message or message_chain:
            self.send_message(data, message, message_chain=message_chain, at=reply.at)

    def image_face(self, data):
        image_id = IM.image(random.choice(self.images), data['type'])
        if image_id:
            chain = [MSG.image(image_id)]
            self.send_message(data, message_chain=chain)


def message_filter(data):
    if data is False:
        return False

    if config['close_beta']['enable']:
        if str(data['group_id']) != str(config['close_beta']['group_id']):
            return False

    for item in ['Q群管家', '小冰']:
        if item in data['text']:
            return False

    black_user = database.user.get_black_user()
    for item in black_user:
        if str(item[0]) == str(data['user_id']):
            return False

    message_speed = database.message.check_message_speed_by_user(data['user_id'], 5)
    if message_speed and message_speed[0] >= 3:
        return False

    return True


def rebuild_message(message):
    data = {
        'text': '',
        'user_id': message['sender']['id'],
        'is_at': False
    }

    if message['type'] == 'FriendMessage':
        # 不接受私聊消息
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
            data['text'] = chain['text'].strip()
        if chain['type'] == 'Image':
            data['image'] = chain['url'].strip()

    return data


def natural_language_processing(message):
    result = NLP.emotion(message)
    if result:
        item = result['items'][0]
        if 'replies' in item and item['replies']:
            return random.choice(item['replies'])
        label = item['label']
        if label == 'neutral':
            return ''
        elif label == 'optimistic':
            return '虽然听不懂博士在说什么，但阿米娅能感受到博士现在高兴的心情，欸嘿嘿……'
        elif label == 'pessimistic':
            return '博士心情不好吗？阿米娅不懂怎么安慰博士，但阿米娅会默默陪在博士身边的'


def call_me(message, only_call=False):
    if only_call:
        if word_in_sentence(message, amiya_name[0]):
            for name in amiya_name[0]:
                message = message.replace(name, '')
            message = re.sub(r'\W', '', message)
            if message == '':
                return True
    else:
        for name in amiya_name[0]:
            if message.find(name) == 0:
                return True
    return False
