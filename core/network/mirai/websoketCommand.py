import json
from abc import ABCMeta, abstractmethod
from typing import List

from core.network.mirai import func_with_name
from core.util import Singleton


class WebsocketCommandClass(metaclass=Singleton):
    class PluginInfoClass(metaclass=Singleton):
        @func_with_name(name='About')
        def About(self, syncId: int = 1):
            return build_command(content=None, command='about', syncId=syncId)

    class MessageCacheClass(metaclass=Singleton):
        @func_with_name(name='MessageFromId')
        def MessageFromId(self, sessionKey: str, messageId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'id': messageId
            }, command='messageFromId', syncId=syncId)

    class AccountInfoClass(metaclass=Singleton):
        @func_with_name(name='FriendList')
        def FriendList(self, sessionKey: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey
            }, command='friendList', syncId=syncId)

        @func_with_name(name='GroupList')
        def GroupList(self, sessionKey: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey
            }, command='groupList', syncId=syncId)

        @func_with_name(name='MemberList')
        def MemberList(self, sessionKey: str, groupId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId
            }, command='memberList', syncId=syncId)

        @func_with_name(name='BotProfile')
        def BotProfile(self, sessionKey: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey
            }, command='botProfile', syncId=syncId)

        @func_with_name(name='FriendProfile')
        def FriendProfile(self, sessionKey: str, friendId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': friendId
            }, command='friendProfile', syncId=syncId)

        @func_with_name(name='MemberProfile')
        def MemberProfile(self, sessionKey: str, groupId: int, memberId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId
            }, command='memberProfile', syncId=syncId)

        @func_with_name(name='UserProfile')
        def UserProfile(self, sessionKey: str, userId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': userId,
            }, command='userProfile', syncId=syncId)

    class MessageSendClass(metaclass=Singleton):
        @func_with_name(name='SendFriendMessage')
        def SendFriendMessage(self, sessionKey: str, friendId: int,
                              messageChain: List[dict], quoteMessageId: int = -1, syncId: int = 1):
            if quoteMessageId == -1:
                return build_command({
                    'sessionKey': sessionKey,
                    'target': friendId,
                    'messageChain': messageChain
                }, command='sendFriendMessage', syncId=syncId)
            return build_command({
                'sessionKey': sessionKey,
                'target': friendId,
                'quote': quoteMessageId,
                'messageChain': messageChain
            }, command='sendFriendMessage', syncId=syncId)

        @func_with_name(name='SendGroupMessage')
        def SendGroupMessage(self, sessionKey: str, groupId: int,
                             messageChain: List[dict], quoteMessageId: int = -1, syncId: int = 1):
            if quoteMessageId == -1:
                return build_command({
                    'sessionKey': sessionKey,
                    'target': groupId,
                    'messageChain': messageChain
                }, command='sendGroupMessage', syncId=syncId)
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'quote': quoteMessageId,
                'messageChain': messageChain
            }, command='sendGroupMessage', syncId=syncId)

        @func_with_name(name='SendTempMessage')
        def SendTempMessage(self, sessionKey: str, groupId: int, memberId: int,
                            messageChain: List[dict], quoteMessageId: int = -1, syncId: int = 1):
            if quoteMessageId == -1:
                return build_command({
                    'sessionKey': sessionKey,
                    'qq': memberId,
                    'group': groupId,
                    'messageChain': messageChain
                }, command='sendTempMessage', syncId=syncId)
            return build_command({
                'sessionKey': sessionKey,
                'qq': memberId,
                'group': groupId,
                'quote': quoteMessageId,
                'messageChain': messageChain
            }, command='sendTempMessage', syncId=syncId)

        @func_with_name(name='SendNudge')
        def SendNudge(self, sessionKey: str, userId: int,
                      subjectId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': userId,
                'subject': subjectId
            }, command='sendNudge', syncId=syncId)

    class MessageRecallClass(metaclass=Singleton):
        @func_with_name(name='RecallMessage')
        def RecallMessage(self, sessionKey: str, messageId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'messageId': messageId
            }, command='recall', syncId=syncId)

    class FileOperateClass(metaclass=ABCMeta):
        @abstractmethod
        def FileList(*args, **kwargs):
            raise NotImplementedError('FileList is not implemented.')

        @abstractmethod
        def FileInfo(*args, **kwargs):
            raise NotImplementedError('FileInfo is not implemented.')

        @abstractmethod
        def FileDelete(*args, **kwargs):
            raise NotImplementedError('FileDelete is not implemented.')

        @abstractmethod
        def FileMove(*args, **kwargs):
            raise NotImplementedError('FileMove is not implemented.')

        @abstractmethod
        def FileRename(*args, **kwargs):
            raise NotImplementedError('FileRename is not implemented.')

        @abstractmethod
        def DirectoryMake(*args, **kwargs):
            raise NotImplementedError('DirectoryMake is not implemented.')

    class AccountManageClass(metaclass=Singleton):
        @func_with_name(name='DeleteFriend')
        def DeleteFriend(self, sessionKey: str, friendId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': friendId
            }, command='deleteFriend', syncId=syncId)

    class AdminOperateClass(metaclass=Singleton):
        @func_with_name(name='Mute')
        def Mute(self, sessionKey: str, groupId: int, memberId: int, time: int = 0, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId,
                'time': time
            }, command='mute', syncId=syncId)

        @func_with_name(name='UnMute')
        def UnMute(self, sessionKey: str, groupId: int, memberId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId,
            }, command='unmute', syncId=syncId)

        @func_with_name(name='Kick')
        def Kick(self, sessionKey: str, groupId: int, memberId: int, msg: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId,
                'msg': msg
            }, command='kick', syncId=syncId)

        @func_with_name(name='Quit')
        def Quit(self, sessionKey: str, groupId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId
            }, command='quit', syncId=syncId)

        @func_with_name(name='MuteAll')
        def MuteAll(self, sessionKey: str, groupId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId
            }, command='muteAll', syncId=syncId)

        @func_with_name(name='UnMuteAll')
        def UnMuteAll(self, sessionKey: str, groupId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId
            }, command='unmuteAll', syncId=syncId)

        @func_with_name(name='SetEssence')
        def SetEssence(self, sessionKey: str, messageId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': messageId
            }, command='setEssence', syncId=syncId)

        @func_with_name(name='GroupConfigGet')
        def GroupConfigGet(self, sessionKey: str, groupId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId
            }, command='groupConfig', subcommand='get', syncId=syncId)

        @func_with_name(name='GroupConfigUpdate')
        def GroupConfigUpdate(self, sessionKey: str, groupId: int, config: dict, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'config': config
            }, command='groupConfig', subcommand='update', syncId=syncId)

        @func_with_name(name='MemberInfoGet')
        def MemberInfoGet(self, sessionKey: str, groupId: int, memberId: int, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId
            }, command='memberInfo', subcommand='get', syncId=syncId)

        @func_with_name(name='MemberInfoUpdate')
        def MemberInfoUpdate(self, sessionKey: str, groupId: int, memberId: int, info: dict, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId,
                'info': info
            }, command='memberInfo', subcommand='update', syncId=syncId)

        @func_with_name(name='')
        def MemberAdmin(self, sessionKey: str, groupId: int, memberId: int, assign: bool, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'target': groupId,
                'memberId': memberId,
                'assgin': assign
            }, command='memberAdmin', syncId=syncId)

    class GroupAnnounceClass(metaclass=Singleton):
        @func_with_name(name='AnnoList')
        def AnnoList(self, groupId: int, offset: int, size: int, syncId: int = 1):
            return build_command({
                'id': groupId,
                'offset': offset,
                'size': size
            }, command='anno_list', syncId=syncId)

        @func_with_name(name='AnnoPublish')
        def AnnoPublish(self, groupId: int, content: str, pinned: bool = False, syncId: int = 1, **kwargs):
            return build_command({
                                     'target': groupId,
                                     'content': content,
                                     'pinned': pinned,
                                 }.update(**kwargs), command='anno_publish', syncId=syncId)

        @func_with_name(name='AnnoDelete')
        def AnnoDelete(self, groupId: int, annoId: int, syncId: int = 1):
            return build_command({
                'id': groupId,
                'fid': annoId
            }, command='anno_delete', syncId=syncId)

    class EventHandleClass(metaclass=Singleton):
        @func_with_name(name='NewFriendRequestEvent')
        def NewFriendRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                  operate: int, msg: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_newFriendRequestEvent', syncId=syncId)

        @func_with_name(name='MemberJoinRequestEvent')
        def MemberJoinRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                   operate: int, msg: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_memberJoinRequestEvent', syncId=syncId)

        @func_with_name(name='BotInvitedJoinGroupRequestEvent')
        def BotInvitedJoinGroupRequestEvent(self, sessionKey: str, eventId: int, fromId: int, groupId: int,
                                            operate: int, msg: str, syncId: int = 1):
            return build_command({
                'sessionKey': sessionKey,
                'eventId': eventId,
                'fromId': fromId,
                'groupId': groupId,
                'operate': operate,
                'message': msg
            }, command='resp_botInvitedJoinGroupRequestEvent', syncId=syncId)

    def __init__(self):
        self.PluginInfo = self.PluginInfoClass()
        self.MessageCache = self.MessageCacheClass()
        self.AccountInfo = self.AccountInfoClass()
        self.MessageSend = self.MessageSendClass()
        self.MessageRecall = self.MessageRecallClass()
        self.AccountManage = self.AccountManageClass()
        self.AdminOperate = self.AdminOperateClass()
        self.GroupAnnounce = self.GroupAnnounceClass()
        self.EventHandle = self.EventHandleClass()

    @classmethod
    def build_command(cls, content, command, subcommand=None, syncId: int = 1):
        if content is None:
            return json.dumps(
                {
                    'syncId': syncId,
                    'command': command,
                    'subCommand': subcommand,
                },
                ensure_ascii=False
            )
        return json.dumps(
            {
                'syncId': syncId,
                'command': command,
                'subCommand': subcommand,
                'content': content
            },
            ensure_ascii=False
        )

    def debug(self):
        print(type(self))


build_command = WebsocketCommandClass.build_command

WebsocketCommand = WebsocketCommandClass()
