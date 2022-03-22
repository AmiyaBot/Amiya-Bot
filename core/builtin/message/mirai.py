from typing import Union
from core.util import remove_punctuation, chinese_to_digits, text_to_pinyin, cut_by_jieba
from core.network import WSOperation
from core.network.httpSessionClient import HttpSessionClient
from core.builtin.message import Message, Event
from core.database.user import User
from core.config import config

from .miraiEventDTO import Friend, Group, Subject, Client, GroupMember

http = HttpSessionClient()


class BotEvents:
    class BotOnlineEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotOfflineEventActive(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotOfflineEventForce(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotOfflineEventDropped(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']

    class BotReloginEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.qq = data['qq']


class FriendEvent:
    class FriendInputStatusChangedEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.friend = Friend(**data['friend'])
            self.inputting = data['inputting']

    class FriendNickChangedEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.friend = Friend(**data['friend'])
            self._from = data['from']
            self.to = data['to']

    class FriendRecallEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.authorId = data['authorId']
            self.messageId = data['messageId']
            self.time = data['time']
            self.operator = data['operator']

    class NewFriendRequestEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.eventId = data['eventId']
            self.fromId = data['fromId']
            self.groupId = data['groupId']
            self.nick = data['nick']
            self.message = data['message']


class GroupEvents:
    class BotGroupPermissionChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])

    class BotMuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.durationSeconds = data['durationSeconds']
            self.operator = GroupMember(data['operator'])

    class BotUnmuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.operator = GroupMember(data['operator'])

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

            self.group = Group(**data['group'])

    class BotLeaveEventActive(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.group = Group(**data['group'])

    class BotLeaveEventKick(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.group = Group(**data['group'])

    class GroupRecallEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.authorId = data['authorId']
            self.messageId = data['messageId']
            self.time = data['time']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class NudgeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.fromId = data['fromId']
            self.target = data['target']
            self.action = data['action']
            self.suffix = data['suffix']
            self.subject = Subject(**data['subject'])

    class GroupNameChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupEntranceAnnouncementChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupMuteAllEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupAllowAnonymousChatEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class GroupAllowConfessTalkEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.isByBot = data['isByBot']
            self.group = Group(**data['group'])

    class GroupAllowMemberInviteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.group = Group(**data['group'])
            self.operator = GroupMember(data['operator'])

    class MemberJoinEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])

    class MemberLeaveEventKick(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class MemberLeaveEventQuit(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])

    class MemberCardChangeEvent(Event):
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

    class MemberPermissionChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.origin = data['origin']
            self.current = data['current']
            self.member = GroupMember(data['member'])

    class MemberMuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.durationSeconds = data['durationSeconds']
            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class MemberUnmuteEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.member = GroupMember(data['member'])
            self.operator = GroupMember(data['operator'])

    class MemberHonorChangeEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.action = data['action']
            self.honor = data['honor']
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


class ClientEvents:
    class OtherClientOnlineEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.client = Client(**data['client'])

    class OtherClientOfflineEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.client = Client(**data['client'])


class CommandEvents:
    class CommandExecutedEvent(Event):
        def __init__(self, data):
            super().__init__(data['type'], data)

            self.name = data['name']
            self.friend = data['friend']
            self.member = data['member']
            self.args = data['args']


class Mirai(BotEvents,
            FriendEvent,
            GroupEvents,
            ClientEvents,
            CommandEvents):
    pass


def mirai_message_formatter(account: int, data: dict, operation: WSOperation = None) -> Union[Message, Event, None]:
    """
    Mirai 消息解析

    :param account:   Bot 账号
    :param data:      Mirai 消息链
    :param operation: Websocket 操作接口
    :return:
    """

    if 'type' not in data:
        return None

    if data['type'] == 'FriendMessage':
        msg = Message(data, operation)
        msg.type = 'friend'
        msg.nickname = data['sender']['nickname']

    elif data['type'] in ['GroupMessage', 'TempMessage']:
        msg = Message(data, operation)
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
                if chain['target'] == account:
                    msg.is_at = True
                    msg.is_call = True
                else:
                    msg.at_target.append(chain['target'])

            if chain['type'] == 'Plain':
                text += chain['text'].strip()

            if chain['type'] == 'Face':
                msg.face.append(chain['faceId'])

            if chain['type'] == 'Image':
                msg.image.append(chain['url'].strip())

    return text_convert(msg, text, text)


def text_convert(msg: Message, origin, initial):
    """
    消息文本的最终处理

    :param msg:     Message 对象
    :param origin:  预处理消息文本
    :param initial: 未经预处理的原始消息文本
    :return:        Message 对象
    """
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
