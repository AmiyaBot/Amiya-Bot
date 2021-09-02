import re
import json
import jieba
import traceback

from core.util import log
from core.util.config import config, keyword
from core.util.common import text_to_pinyin, remove_punctuation, make_folder
from core.util.numberTranslate import chinese_to_digits
from core.database.models import User, Group

CONF = config()
NAME = keyword('name')


class Message:
    """
    解析 mirai 消息链为一切可用的信息
    """
    user_info: User
    group_info: Group

    def __init__(self, message=None, _format=True):
        self.type = ''
        self.text = ''
        self.face = []
        self.image = ''
        self.text_ori = ''
        self.text_digits = ''
        self.text_cut = ''
        self.text_cut_pinyin = ''

        self.at_target = ''

        self.is_at = False
        self.is_call = False
        self.is_bad_call = False
        self.is_only_call = False
        self.is_new_user = False
        self.is_new_group = False
        self.is_admin = False
        self.is_group_admin = False
        self.is_black = False
        self.is_event = False

        self.bad_name = ''

        self.user_id = ''
        self.group_id = ''
        self.nickname = ''
        self.event_name = ''

        self.message = message

        if _format and message is not None:
            self.__format_message()

    @staticmethod
    def cut_words(text):
        return jieba.lcut(
            text.lower().replace(' ', '')
        )

    def __format_message(self):
        data = self.message

        if 'type' not in data:
            return False

        if data['type'] == 'FriendMessage':
            self.type = 'friend'
            self.nickname = data['sender']['nickname']

        elif data['type'] == 'GroupMessage':
            self.type = 'group'
            self.group_id = data['sender']['group']['id']
            self.nickname = data['sender']['memberName']
            self.is_group_admin = data['sender']['permission'] in ['OWNER', 'ADMINISTRATOR']

            self.group_info, self.is_new_group = Group.get_or_create(group_id=self.group_id)

        else:
            self.is_event = True
            self.event_name = data['type']
            self.__save_events_file()
            return False

        self.user_id = data['sender']['id']
        self.user_info, self.is_new_user = User.get_or_create(user_id=self.user_id)

        self.is_admin = self.user_id == CONF['adminId']
        self.is_black = bool(self.user_info.black)

        self.__trans_text(message_chain=data['messageChain'])

        self.__check_call()

    def __trans_text(self, text='', message_chain=None):
        if message_chain:
            for chain in message_chain:
                if chain['type'] == 'At':
                    self.at_target = chain['target']
                    if self.at_target == CONF['selfId']:
                        self.is_at = True

                if chain['type'] == 'Plain':
                    text += chain['text'].strip()

                if chain['type'] == 'Face':
                    self.face.append(chain['faceId'])

                if chain['type'] == 'Image':
                    self.image = chain['url'].strip()

        self.text = remove_punctuation(text)
        self.text_digits = chinese_to_digits(self.text)

        chars = self.cut_words(self.text) + self.cut_words(self.text_digits)
        words = list(set(chars))
        words = sorted(words, key=chars.index)
        # words = sorted(words, reverse=True, key=lambda i: len(i))

        self.text_ori = text
        self.text_cut = words
        self.text_cut_pinyin = [text_to_pinyin(char) for char in words]

    def __check_call(self):
        text = self.text

        for item in NAME['bad'].split(','):
            if text.startswith(item):
                self.bad_name = item
                self.is_bad_call = True
                break

        for item in NAME['good'].split(','):
            if text.startswith(item):
                self.is_call = True

            text = text.replace(item, '')

        text = re.sub(r'\W', '', text).strip()
        if text == '' and (self.is_at or self.is_call):
            self.is_only_call = True

    def __save_events_file(self):
        # noinspection PyBroadException
        try:
            path = 'log/events'
            make_folder(path)

            with open(f'{path}/{self.event_name}.json', mode='w+', encoding='utf-8') as remind:
                remind.write(json.dumps(self.message, ensure_ascii=False))

        except Exception:
            log.error(traceback.format_exc())
