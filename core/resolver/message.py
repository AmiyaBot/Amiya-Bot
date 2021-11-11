import re
import json
import jieba
import traceback

from typing import List

from core.util import log
from core.config import config, keyword
from core.util.common import text_to_pinyin, remove_punctuation, make_folder
from core.util.numberTranslate import chinese_to_digits
from core.database.models import User, GroupActive, ReplaceText


class Message:
    """
    解析 mirai 消息链为一切可用的信息
    """
    user_info: User
    group_active: GroupActive

    def __init__(self, message=None, _format=True):
        self.message_id = None

        self.type = ''
        self.text = ''
        self.face = []
        self.image = ''
        self.text_origin = ''
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
        self.raw_chain = ''

        self.message = message

        if _format and message is not None:
            self.__format_message()

    @staticmethod
    def cut_words(text):
        return jieba.lcut(
            text.lower().replace(' ', '')
        )

    @staticmethod
    def remove_name(text):
        for item in keyword.name.good:
            if text.startswith(item):
                return text.replace(item, '', 1)
        return text

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

            self.group_active, self.is_new_group = GroupActive.get_or_create(group_id=self.group_id)

        else:
            self.is_event = True
            self.event_name = data['type']
            self.__save_events_file()
            return False

        self.user_id = data['sender']['id']
        self.user_info, self.is_new_user = User.get_or_create(user_id=self.user_id)

        self.is_admin = self.user_id == config.account.admin
        self.is_black = bool(self.user_info.black)

        self.__trans_text(message_chain=data['messageChain'])

        self.__check_call()

    def __trans_text(self, text='', message_chain=None):
        if message_chain:
            self.raw_chain = message_chain[1:]
            for chain in message_chain:
                if chain['type'] == 'Source':
                    self.message_id = chain['id']

                if chain['type'] == 'At':
                    self.at_target = chain['target']
                    if self.at_target == config.account.bot:
                        self.is_at = True
                        self.is_call = True

                if chain['type'] == 'Plain':
                    text += chain['text'].strip()

                if chain['type'] == 'Face':
                    self.face.append(chain['faceId'])

                if chain['type'] == 'Image':
                    self.image = chain['url'].strip()

        self.text_origin = text

        replace: List[ReplaceText] = ReplaceText.select() \
            .where(ReplaceText.group_id == self.group_id, ReplaceText.is_active == 1) \
            .orwhere(ReplaceText.is_global == 1)

        if replace:
            for item in reversed(list(replace)):
                text = text.replace(item.target, item.origin)

        self.text = remove_punctuation(text)
        self.text_digits = chinese_to_digits(self.text)

        chars = self.cut_words(self.text) + self.cut_words(self.text_digits)
        words = list(set(chars))
        words = sorted(words, key=chars.index)
        # words = sorted(words, reverse=True, key=lambda i: len(i))

        self.text_cut = words
        self.text_cut_pinyin = [text_to_pinyin(char) for char in words]

    def __check_call(self):
        text = self.text

        for item in keyword.name.bad:
            if text.startswith(item):
                self.bad_name = item
                self.is_bad_call = True
                break

        for item in keyword.name.good:
            if not self.is_call and text.startswith(item):
                self.is_call = True

            if item != '阿米娅' or (item == '阿米娅' and text.startswith(item)):
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
