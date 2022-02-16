import collections

from typing import *
from core.util import remove_punctuation, chinese_to_digits, text_to_pinyin, cut_by_jieba
from core.network import WSOperation
from core.network.httpSessionClient import HttpSessionClient
from core.builtin.message import Message, Event
from core.database.user import User
from core.config import config

group = collections.namedtuple('group', ['id', 'name', 'permission'])
friend = collections.namedtuple('friend', ['id', 'nickname', 'remark'])
subject = collections.namedtuple('subject', ['id', 'kind'])

http = HttpSessionClient()


class GroupMember:
    def __init__(self, data):
        self.id = data['id']
        self.memberName = data['memberName']
        self.specialTitle = data['specialTitle']
        self.permission = data['permission']
        self.joinTimestamp = data['joinTimestamp']
        self.lastSpeakTimestamp = data['lastSpeakTimestamp']
        self.muteTimeRemaining = data['muteTimeRemaining']
        self.group = group(**data['group'])


class Mirai:
    class BotGroupPermissionChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = group(**data['group'])

    class BotInvitedJoinGroupRequestEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.eventId = data['eventId']
            self.message = data['message']
            self.fromId = data['fromId']
            self.groupId = data['groupId']
            self.groupName = data['groupName']
            self.nick = data['nick']

        async def handle(self, allow: bool = False, message: str = ''):
            await http.post('/resp/botInvitedJoinGroupRequestEvent', {
                'sessionKey': http.session,
                'eventId': self.eventId,
                'fromId': self.fromId,
                'groupId': self.groupId,
                'operate': 0 if allow else 1,
                'message': message
            })

    class BotJoinGroupEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.group = group(**data['group'])

    class BotLeaveEventActive(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.group = group(**data['group'])

    class BotLeaveEventKick(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.group = group(**data['group'])

    class BotMuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.durationSeconds = data['durationSeconds']
            self.operator = GroupMember(data['operator'])

    class BotOfflineEventDropped(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotOnlineEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotReloginEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class GroupAllowAnonymousChatEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupAllowConfessTalkEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.isByBot = data['isByBot']
            self.group = group(**data['group'])

    class GroupMuteAllEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupNameChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupRecallEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.authorId = data['authorId']
            self.messageId = data['messageId']
            self.time = data['time']
            self.group = group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class MemberCardChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.member = GroupMember(data['member'])

    class MemberHonorChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.action = data['action']
            self.honor = data['honor']
            self.member = GroupMember(data['member'])

    class MemberJoinEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])

    class MemberJoinRequestEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.eventId = data['eventId']
            self.message = data['message']
            self.fromId = data['fromId']
            self.groupId = data['groupId']
            self.groupName = data['groupName']
            self.nick = data['nick']

    class MemberLeaveEventKick(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class MemberLeaveEventQuit(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])

    class MemberMuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.durationSeconds = data['durationSeconds']
            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class MemberPermissionChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.member = GroupMember(data['member'])

    class MemberSpecialTitleChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.member = GroupMember(data['member'])

    class MemberUnmuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class NudgeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.fromId = data['fromId']
            self.target = data['target']
            self.action = data['action']
            self.suffix = data['suffix']
            self.subject = subject(**data['subject'])

    @classmethod
    def mirai_message_formatter(cls, account: int, data: dict, opration: WSOperation) -> Union[Message, Event, None]:
        """
        Mirai 消息解析函数

        :param account:  Bot 账号
        :param data:     Mirai 消息链
        :param opration: Websocket 操作接口
        :return:
        """

        if 'type' not in data:
            return None

        if data['type'] == 'FriendMessage':
            msg = Message(data, opration)
            msg.type = 'friend'
            msg.nickname = data['sender']['nickname']

        elif data['type'] in ['GroupMessage', 'TempMessage']:
            msg = Message(data, opration)
            msg.type = 'group' if data['type'] == 'GroupMessage' else 'temp'
            msg.group_id = data['sender']['group']['id']
            msg.nickname = data['sender']['memberName']
            msg.is_group_admin = data['sender']['permission'] in ['OWNER', 'ADMINISTRATOR']

        else:
            if hasattr(Mirai, data['type']):
                msg = getattr(Mirai, data['type'])(data)
            else:
                msg = Event(data['type'], data)
            return msg

        msg.user_id = data['sender']['id']
        msg.user, msg.is_new_user = User.get_or_create(user_id=msg.user_id)

        if msg.user_id in config.admin.accounts:
            msg.is_admin = True

        message_chain = data['messageChain']
        text = ''

        if message_chain:
            msg.raw_chain = message_chain[1:]

            for chain in message_chain:
                if chain['type'] == 'Source':
                    msg.message_id = chain['id']

                if chain['type'] == 'At':
                    msg.at_target = chain['target']
                    if msg.at_target == account:
                        msg.is_at = True
                        msg.is_call = True

                if chain['type'] == 'Plain':
                    text += chain['text'].strip()

                if chain['type'] == 'Face':
                    msg.face.append(chain['faceId'])

                if chain['type'] == 'Image':
                    msg.image.append(chain['url'].strip())

        return text_convert(msg, text, text)


def text_convert(msg: Message, origin, initial):
    msg.text = remove_punctuation(origin)
    msg.text_digits = chinese_to_digits(msg.text)
    msg.text_origin = origin
    msg.text_initial = initial

    chars = cut_by_jieba(msg.text) + cut_by_jieba(msg.text_digits)
    words = list(set(chars))
    words = sorted(words, key=chars.index)

    msg.text_cut = words
    msg.text_cut_pinyin = [text_to_pinyin(char) for char in words]

    return msg
